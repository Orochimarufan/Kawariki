// Allow loading of already-decrypted assets in encrypted game
// MZ version
"use strict";

(function () {
    const inject = function() {
        console.log("Setting up MZ Decrypted Assets...");

        // Imports
        const fs = require('fs');
        const path = require('path');

        // Cache
        const root = path.dirname(new URL(document.baseURI).pathname).substring(1);
        const cache = {}; // path -> bool, true when already decrypted

        // Constants
        const NEVER = 0;
        const ALWAYS = 1;
        const MAYBE = 2;

        const ENCRYPTED_HEADER = Uint8Array.of(0x52,0x50,0x47,0x4d,0x56,0,0,0,0,3,1,0,0,0,0,0);

        // ================== Machinery ===================
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
            if (fs.existsSync(path.join(root, url + "_")))
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
            console.log("Request", url);
            const decrypted = decrypt !== ALWAYS;
            const real_url = (decrypted || url.endsWith("_")) ? url : url + "_";
            const xhr = new XMLHttpRequest();
            xhr.responseType = 'arraybuffer';
            xhr.open('GET', real_url);
            xhr.onload = function() {
                if (xhr.status < 400) {
                    cache[url] = decrypted;
                    resolve(xhr, decrypted);
                } else if (decrypt === MAYBE) {
                    request(url, ALWAYS, resolve, reject);
                } else {
                    reject(xhr);
                }
            };
            // Retry using the encrypted filename on error if we weren't sure
            xhr.onerror = decrypt === MAYBE? function() {
                request(url, ALWAYS, resolve, reject);
            } : reject;
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
            if (decrypted === undefined)
                decrypted = !xhr.responseURL.endsWith("_");
            if (!decrypted)
                buf = Utils.decryptArrayBuffer(buf);
            return buf;
        };

        /**
         * Check if buffer has a RPGMaker MZ encryption header
         * There isn't a built-in way to compare ArrayBuffer or Uint8Array to each other
         * @param {ArrayBuffer} buffer Data
         */
        function is_data_encrypted(buffer) {
            if (buffer.byteLength < ENCRYPTED_HEADER.length)
                return false;
            const header = new Uint8Array(buffer, 0, ENCRYPTED_HEADER.length);
            for (let i = 0; i < header.length; i++) {
                if (ENCRYPTED_HEADER[i] !== header[i])
                    return false;
            }
            return true;
        }

        /**
         * Perform decryption on array buffer
         * @param {ArrayBuffer} buffer
         * @returns {ArrayBuffer}
         */
        function maybe_decrypt_data(buffer) {
            if (is_data_encrypted(buffer))
                return Utils.decryptArrayBuffer(buffer);
            else
                return buffer;
        }

        // ================== Images ======================
        /**
         * Initiate loading of an image
         */
        Bitmap.prototype._startLoading = function() {
            this._image = new Image();
            this._image.onload = this._onLoad.bind(this);
            this._image.onerror = this._onError.bind(this);
            this._destroyCanvas();
            this._loadingState = "loading";
            const decrypt = need_decrypt(this._url, Utils.hasEncryptedImages());
            if (decrypt !== NEVER) {
                this._startDecrypting(decrypt);
            } else {
                this._image.src = this._url;
            }
        };

        /**
         * Retrieve possibly encrypted asset via XHR
         * @param {0|1|2|undefined} decrypt Whether we need to decrypt
         * @note May be modified in plugins, so don't just skip calling it.
         */
        Bitmap.prototype._startDecrypting = function(decrypt) {
            request(
                this._url,
                decrypt ?? need_decrypt(this._url, Utils.hasEncryptedAudio()),
                this._onXhrLoad.bind(this),
                this._onError.bind(this)
            );
        };

        /**
         * Process possibly encrypted XHR response
         * @param {XMLHttpRequest} xhr
         * @param {boolean|undefined} decrypted
         * @note Should we just omit decrypted and infer from responseURL?
         * @note May be modified in plugins, so don't just skip calling it.
         */
        Bitmap.prototype._onXhrLoad = function(xhr, decrypted) {
            if (xhr.status < 400) {
                const arrayBuffer = maybe_decrypt(xhr, decrypted);
                const blob = new Blob([arrayBuffer]);
                this._image.src = URL.createObjectURL(blob);
            } else {
                this._onError();
            }
        };

        // ================== WebAudio ====================
        /**
         * Start loading an audio file
         * @note Is there any reason to use fetch() instead?
         */
         WebAudio.prototype._startLoading = function() {
            if (!WebAudio._context)
                return;
            this._startXhrLoading(this._url);
            const currentTime = WebAudio._currentTime();
            this._lastUpdateTime = currentTime - 0.5;
            this._isError = false;
            this._isLoaded = false;
            this._destroyDecoder();
            if (this._shouldUseDecoder()) {
                this._createDecoder();
            }
        };

        /**
         * Send off a XHR to load audio
         * @param {string} url The audio file URL
         */
        WebAudio.prototype._startXhrLoading = function(url) {
            if (url.endsWith("_"))
                url = url.substring(0, url.length-1);
            request(
                url,
                need_decrypt(url, Utils.hasEncryptedAudio()),
                this._onXhrLoad.bind(this),
                this._onError.bind(this)
            );
        };

        /**
         * Possibly decrypt audio buffer
         */
         WebAudio.prototype._readableBuffer = function() {
            return maybe_decrypt_data(this._data.buffer);
        };

        /**
         * Only for improved plugin compat
         * @returns The (hopefully) real URL
         */
         WebAudio.prototype._realUrl = function() {
            return this._url + (need_decrypt(this._url, Utils.hasEncryptedAudio()) === ALWAYS ? "_" : "");
        };
    };

    // Inject after rmmz_core.js
    const observer = new MutationObserver(function(mutations) {
        for (const m of mutations) {
            for (const e of m.addedNodes) {
                if (e.nodeType === Node.ELEMENT_NODE && e.tagName === "SCRIPT" && e.src !== '') {
                    const src = new URL(e.src);
                    if (src.pathname.endsWith("js/rmmz_core.js")) {
                        e.addEventListener("load", inject);
                    }
                }
            }
        }
    });
    observer.observe(document, {
        childList: true,
        subtree: true,
    });
    document.addEventListener("load", observer.disconnect);
})();
