// Allow loading of already-decrypted assets in encrypted game
"use strict";

(function () {
    const inject = function() {
        console.log("Apply mv-decrypted-assets.js");
        const fs = require('fs');
        const path = require('path');
        const root = path.dirname(new URL(document.baseURI).pathname).substring(1);
        const cache = {}; // path -> bool, true when already decrypted
        // Constants
        const NEVER = 0;
        const ALWAYS = 1;
        const MAYBE = 2;
        /**
         * Determine if an URL needs to be decrypted
         * @param {string} url URL to load
         * @param {boolean|undefined} hasEncrypted Decrypter.hasEncrypted* constant
         * @returns {0|1|2} One of NEVER, ALWAYS or MAYBE
         */
        function need_decrypt(url, hasEncrypted) {
            // Are there even encrypted items
            if (hasEncrypted === false)
                return NEVER;
            // Check cache
            const cached = cache[url];
            if (cached !== undefined)
                return cached? NEVER : ALWAYS;
            // Try to check filesystem paths
            // XXX: is this actually faster than just doing 2 XHRs?
            if (fs.existsSync(path.join(root, url)))
                return NEVER;
            if (fs.existsSync(path.join(root, Decrypter.extToEncryptExt(url))))
                return ALWAYS;
            // Brute-force-try both, could be case mismatch
            return MAYBE;
        };
        /**
         * Request a possibly encrypted resource as arraybuffer
         * @param {string} url URL to load
         * @param {0|1|2} decrypt need_decrypt() for url
         * @param {(a: XMLHttpRequest, decrypted: boolean) => void} resolve Success callback
         * @param {(e: any) => void} reject Failure callback
         */
        function request(url, decrypt, resolve, reject) {
            const decrypted = decrypt !== ALWAYS;
            const real_url = decrypted ? url : Decrypter.extToEncryptExt(url);
            const xhr = new XMLHttpRequest();
            xhr.responseType = 'arraybuffer';
            xhr.open('GET', real_url);
            xhr.onload = function() {
                if (xhr.status < 400) {
                    cache[url] = decrypted;
                    resolve(xhr, decrypted);
                }
            };
            // Retry using the encrypted filename on error if we weren't sure
            xhr.onerror = decrypt === MAYBE? request.bind(this, url, ALWAYS, resolve, reject) : reject;
            xhr.send();
        };
        /**
         * Perform decryption on result from request()
         * @param {XMLHttpRequest} xhr 
         * @param {boolean|undefined} decrypted 
         * @returns {ArrayBuffer}
         */
        function maybe_decrypt(xhr, decrypted) {
            let buf = xhr.response;
            if (!decrypted)
                buf = Decrypter.decryptArrayBuffer(buf);
            return buf;
        };
        Decrypter._mda_request = request;
        Decrypter._mda_need_decrypt = need_decrypt;
        Decrypter._mda_maybe_decrypt = maybe_decrypt;
        // Images
        /**
         * @typedef {{_loadListener: (a) => void, _errorListener: (e) => void, _loader: any, _image: HTMLImageElement}} Bitmap
         * @param {string} url 
         * @param {Bitmap} bitmap 
         */
        Decrypter.decryptImg = function(url, bitmap) {
            const decrypt = need_decrypt(url, Decrypter.hasEncryptedImages);
            const errhand = bitmap._loader || Bitmap.prototype._onError.bind(bitmap);
            if (decrypt === NEVER) {
                bitmap._image.src = url;
                bitmap._image.addEventListener('load', bitmap._loadListener = function(ev) {
                    cache[url] = true;
                    Bitmap.prototype._onLoad.call(bitmap, ev);
                });
                bitmap._image.addEventListener('error', bitmap._errorListener = errhand);
            } else {
                request(
                    url,
                    decrypt,
                    function(xhr, decrypted) {
                        bitmap._image.src = Decrypter.createBlobUrl(maybe_decrypt(xhr, decrypted));
                        bitmap._image.addEventListener('load', bitmap._loadListener = Bitmap.prototype._onLoad.bind(bitmap));
                        bitmap._image.addEventListener('error', bitmap._errorListener = errhand);
                    },
                    errhand
                );
            }
        };
        // WebAudio
        /**
         * @param {string} url 
         */
        WebAudio.prototype._load = function(url) {
            if (!WebAudio._context)
                return;
            request(
                url,
                need_decrypt(url, Decrypter.hasEncryptedAudio),
                this._onXhrLoad.bind(this),
                this._loader || function(){this._hasError = true;}.bind(this)
            );
        };
        /**
         * May be modified in plugins, so don't just skip calling it.
         * @param {XMLHttpRequest} xhr 
         * @param {boolean|undefined} decrypted 
         * @note How likely is it for the decrypted argument to get lost in transit?
         *       We can probably infer it with decent reliability from the RPGMV header.
         */
        WebAudio.prototype._onXhrLoad = function(xhr, decrypted) {
            const array = maybe_decrypt(xhr, decrypted);
            this._readLoopComments(new Uint8Array(array));
            WebAudio._context.decodeAudioData(array, function(buffer) {
                this._buffer = buffer;
                this._totalTime = buffer.duration;
                if (this._loopLength > 0 && this._sampleRate > 0) {
                    this._loopStart /= this._sampleRate;
                    this._loopLength /= this._sampleRate;
                } else {
                    this._loopStart = 0;
                    this._loopLength = this._totalTime;
                }
                this._onLoad();
            }.bind(this));
        };
    };

    // Inject before plugins.js
    const observer = new MutationObserver(function(mutations) {
        for (const m of mutations) {
            for (const e of m.addedNodes) {
                if (e.nodeType === Node.ELEMENT_NODE && e.tagName === "SCRIPT" && e.src !== '') {
                    const src = new URL(e.src);
                    if (src.pathname.endsWith("js/plugins.js")) {
                        const script = document.createElement("script");
                        script.textContent = "(" + inject.toString() + ")();"
                        e.insertAdjacentElement("beforebegin", script);
                        observer.disconnect();
                        return;
                    }
                }
            }
        }
    });
    observer.observe(document, {
        childList: true,
        subtree: true,
    });
    document.addEventListener("DOMContentLoaded", observer.disconnect);
})();
