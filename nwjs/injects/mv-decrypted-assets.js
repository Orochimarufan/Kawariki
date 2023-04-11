// Allow loading of already-decrypted assets in encrypted game
"use strict";

(function () {
    const fs = require('fs');
    const path = require('path');

    // Constants
    const NEVER = 0;
    const ALWAYS = 1;
    const MAYBE = 2;

    const MDA = {
        // Data
        root: path.dirname(new URL(document.baseURI).pathname).substring(1),
        cache: {},

        // Constants
        NEVER,
        ALWAYS,
        MAYBE,

        /**
         * Determine if an URL needs to be decrypted
         * @param {string} url URL to load
         * @param {boolean|undefined} hasEncrypted Decrypter.hasEncrypted* constant
         * @returns {0|1|2} One of NEVER, ALWAYS or MAYBE
         */
        _need_decrypt(url, hasEncrypted) {
            // Are there even encrypted items
            if (hasEncrypted === false)
                return NEVER;
            // Check cache
            const cached = this.cache[url];
            if (cached !== undefined)
                return cached? NEVER : ALWAYS;
            // Try to check filesystem paths
            // XXX: is this actually faster than just doing 2 XHRs?
            url = decodeURIComponent(url);
            if (fs.existsSync(path.join(this.root, url)))
                return NEVER;
            if (fs.existsSync(path.join(this.root, Decrypter.extToEncryptExt(url))))
                return ALWAYS;
            // Brute-force-try both, could be case mismatch
            return MAYBE;
        },
        need_decrypt(url, he) {
            const r = this._need_decrypt(url, he);
            if (r != NEVER) console.log(url, he, r);
            return r;
        },
        /**
         * Request a possibly encrypted resource as arraybuffer
         * @param {string} url URL to load
         * @param {0|1|2} decrypt need_decrypt() for url
         * @param {(a: XMLHttpRequest, decrypted: boolean) => void} resolve Success callback
         * @param {(e: any) => void} reject Failure callback
         */
        request(url, decrypt, resolve, reject) {
            const decrypted = decrypt !== ALWAYS;
            const real_url = decrypted ? url : Decrypter.extToEncryptExt(url);
            const xhr = new XMLHttpRequest();
            xhr.responseType = 'arraybuffer';
            xhr.open('GET', real_url);
            xhr.onload = () => {
                if (xhr.status < 400) {
                    this.cache[url] = decrypted;
                    resolve(xhr, decrypted);
                }
            };
            // Retry using the encrypted filename on error if we weren't sure
            xhr.onerror = decrypt === MAYBE? this.request.bind(this, url, ALWAYS, resolve, reject) : reject;
            xhr.send();
        },
        /**
         * Perform decryption on result from request()
         * @param {XMLHttpRequest} xhr
         * @param {boolean|undefined} decrypted
         * @returns {ArrayBuffer}
         */
        maybe_decrypt(xhr, decrypted) {
            let buf = xhr.response;
            if (!decrypted)
                buf = Decrypter.decryptArrayBuffer(buf);
            return buf;
        },
        /**
         * Patch the rpgmaker core library
         */
        patchCore() {
            console.log("[mv-decrypted-assets] Patching RPGMaker Core");
            const mda = this;
            // Images
            /**
             * @typedef {{_loadListener: (a) => void, _errorListener: (e) => void, _loader: any, _image: HTMLImageElement}} Bitmap
             * @param {string} url
             * @param {Bitmap} bitmap
             */
            Decrypter.decryptImg = function(url, bitmap) {
                const decrypt = mda.need_decrypt(url, Decrypter.hasEncryptedImages);
                const errhand = bitmap._loader || Bitmap.prototype._onError.bind(bitmap);
                if (decrypt === NEVER) {
                    bitmap._image.src = url;
                    bitmap._image.addEventListener('load', bitmap._loadListener = function(ev) {
                        mda.cache[url] = true;
                        Bitmap.prototype._onLoad.call(bitmap, ev);
                    });
                    bitmap._image.addEventListener('error', bitmap._errorListener = errhand);
                } else {
                    mda.request(
                        url,
                        decrypt,
                        function(xhr, decrypted) {
                            bitmap._image.src = Decrypter.createBlobUrl(mda.maybe_decrypt(xhr, decrypted));
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
                mda.request(
                    url,
                    mda.need_decrypt(url, Decrypter.hasEncryptedAudio),
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
                const array = mda.maybe_decrypt(xhr, decrypted);
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

            // Setup plugin patching
            /**
             * @param {string} name
             */
            PluginManager.loadScript = function(name) {
                //if (/YEP_X_CoreUpdatesOpt/.test(name)) return;
                var url = this._path + name;
                var script = document.createElement('script');
                script.type = 'text/javascript';
                script.src = url;
                script.async = false;
                script.onerror = this.onError.bind(this);
                script._url = url;
                // Patch
                let from = url.lastIndexOf('/');
                from = from >= 0 ? from+1 : 0;
                let to = url.lastIndexOf('.');
                to = to >= from ? to : url.length;
                const basename = url.substring(from, to);
                if (mda.plugins.hasOwnProperty(basename)) {
                    script.addEventListener("load", mda.plugins[basename].bind(script, mda));
                }
                document.body.appendChild(script);
            };
        },
        /** @type {Record<string, (mda: typeof MDA) => void>} */
        plugins: {
            ApngPicture(mda) {
                console.log("[mv-decrypted-assets] Patching APngLoader");
                const _setupApngLoaderIfNeed = SceneManager.setupApngLoaderIfNeed;
                SceneManager.setupApngLoaderIfNeed = function() {
                    // Extract ApngLoader class
                    const stub_loader = {load: () => {}, add: () => {}, onComplete: {add: () => {}}};
                    const PIXI_loader = PIXI.loader;
                    PIXI.loader = stub_loader;
                    _setupApngLoaderIfNeed.call(stub_loader);
                    PIXI.loader = PIXI_loader;
                    const ApngLoader = stub_loader._apngLoaderPicture.constructor;
                    // Patch
                    ApngLoader.prototype.addImage = function(item, option) {
                        var name = String(item.FileName) || '';
                        var ext = mda.need_decrypt(`img/${this._folder}/${name}.png`, Decrypter.hasEncryptedImages) === ALWAYS ? 'rpgmvp' : 'png';
                        name = name.replace(/\.gif$/gi, function() {
                            ext = 'gif';
                            return '';
                        });
                        var path = name.match(/http:/) ? name : `img/${this._folder}/${name}.${ext}`;
                        if (!this._fileHash.hasOwnProperty(name)) {
                            this._fileHash[name] = ApngLoader.convertDecryptExt(path);
                            this._cachePolicy[name] = item.CachePolicy;
                            this._options[name] = item;
                            PIXI.loader.add(path, option);
                        }
                    }
                    // Actually call for real
                    _setupApngLoaderIfNeed.call(this);
                }
            },
            DKTools(mda) {
                console.log("[mv-decrypted-assets] Patching DKTools");
                DKTools.IO.Entity.prototype.isFile = function() {
                    if (this instanceof DKTools.IO.File) {
                        if (DKTools.IO.isLocalMode()) {
                            if (this.isAudio()) {
                                return mda.need_decrypt(this.getFullPath(), Decrypter.hasEncryptedAudio) !== MAYBE;
                            } else if (this.isImage()) {
                                return mda.need_decrypt(this.getFullPath(), Decrypter.hasEncryptedImages) !== MAYBE;
                            } else {
                                return DKTools.IO.isFile(this.getFullPath());
                            }
                        } else {
                            return !!this.hasExtension();
                        }
                    }

                    return false;
                };
                DKTools.IO.File.prototype.exists = function() {
                    if (DKTools.IO.isLocalMode()) {
                        if (this.isAudio()) {
                            return mda.need_decrypt(this.getFullPath(), Decrypter.hasEncryptedAudio) !== MAYBE;
                        } else if (this.isImage()) {
                            return mda.need_decrypt(this.getFullPath(), Decrypter.hasEncryptedImages) !== MAYBE;
                        }
                    }

                    return DKTools.IO.Entity.prototype.exists.call(this);
                };
            },
        },
    };

    window.__MDA = MDA;

    // Inject before plugins.js
    const observer = new MutationObserver(function(mutations) {
        for (const m of mutations) {
            for (const e of m.addedNodes) {
                if (e.nodeType === Node.ELEMENT_NODE && e.tagName === "SCRIPT" && e.src !== '') {
                    const src = new URL(e.src);
                    if (src.pathname.endsWith("js/plugins.js")) {
                        const script = document.createElement("script");
                        script.textContent = "window.__MDA.patchCore();";
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
