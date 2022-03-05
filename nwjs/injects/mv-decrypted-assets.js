// Allow loading of already-decrypted assets in encrypted game
"use strict";

(function () {
    const inject = function() {
        console.log("Apply mv-decrypted-assets.js");
        const fs = require('fs');
        const path = require('path');
        const root = path.dirname(new URL(document.baseURI).pathname).substring(1);
        const Decrypter_decryptImg = Decrypter.decryptImg;
        const cache = {};
        // Images
        Decrypter.decryptImg = function(url, bitmap) {
            if (cache[url] === true || fs.existsSync(path.join(root, url))) {
                cache[url] = true;
                bitmap._image.src = url;
                bitmap._image.addEventListener('load', bitmap._loadListener = Bitmap.prototype._onLoad.bind(bitmap));
                bitmap._image.addEventListener('error', bitmap._errorListener = bitmap._loader || Bitmap.prototype._onError.bind(bitmap));
            } else if (cache[url] === false || fs.existsSync(path.join(root, Decrypter.extToEncryptExt(url)))) {
                cache[url] = false;
                Decrypter_decryptImg.call(this, url, bitmap);
            } else {
                // Try anyway, could be case mismatch
                bitmap._image.src = url;
                bitmap._image.addEventListener('load', bitmap._loadListener = function(ev) {
                    cache[url] = true;
                    bitmap._onLoad(ev);
                });
                bitmap._image.addEventListener('error', bitmap._errorListener = function() {
                    cache[url] = false;
                    Decrypter_decryptImg.call(this, url, bitmap);
                }.bind(this));
            }
        };
        // WebAudio
        const NEVER = 0;
        const ALWAYS = 1;
        const MAYBE = 2;
        WebAudio.prototype._load = function(url) {
            if (!WebAudio._context) return;
            if (!Decrypter.hasEncryptedAudio || cache[url] === true || fs.existsSync(path.join(root, url))) {
                this._mda_really_load(url, NEVER);
            } else if (cache[url] === false || fs.existsSync(path.join(root, Decrypter.extToEncryptExt(url)))) {
                this._mda_really_load(url, ALWAYS);
            } else {
                // Try anyway, could be case mismatch
                this._mda_really_load(url, MAYBE);
            }
        }
        WebAudio.prototype._mda_really_load = function (url, decrypt) {
            const xhr = new XMLHttpRequest();
            const need_decrypt = decrypt === ALWAYS;
            xhr.open('GET', need_decrypt ? Decrypter.extToEncryptExt(url) : url);
            xhr.responseType = 'arraybuffer';
            xhr.onload = function() {
                if (xhr.status < 400) {
                    cache[url] = !need_decrypt;
                    this._onXhrLoad(xhr, need_decrypt);
                }
            }.bind(this);
            if (decrypt === MAYBE)
                xhr.onerror = this._mda_really_load.bind(this, url, ALWAYS);
            else
                xhr.onerror = this._loader || function(){this._hasError = true;}.bind(this);
            xhr.send();
        }
        WebAudio.prototype._onXhrLoad = function(xhr, decrypt) {
            var array = xhr.response;
            if (Decrypter.hasEncryptedAudio && decrypt !== false)
                array = Decrypter.decryptArrayBuffer(array);
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
    const observer = new MutationObserver((mutations) => {
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
    document.addEventListener("DOMContentLoaded", ()=>observer.disconnect());
})();
