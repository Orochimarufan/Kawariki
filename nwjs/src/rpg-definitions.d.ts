// ==================================================================
// RpgMaker Engine types

// ------------------------------------------------------------------
// Input
declare type Input_Action = 'tab'|'shift'|'control'|'escape'|'debug'|'pageup'|'pagedown'|'up'|'left'|'down'|'right'|'ok';
declare type Input_KeyMapper = Record<number, Input_Action|string>;

declare var Input: {
    keyMapper: Input_KeyMapper,
    // Yanfly ButtonCommonEvents:
    _switchButton?: (button: string) => void,
    _revertButton?: (button: string) => void,
};

// ------------------------------------------------------------------
// Configuration & Plugins
declare var ConfigManager: {
    // Yanfly KeyboardConfig:
    keyMapper?: Input_KeyMapper,
    wasdMap?: Input_KeyMapper,
    defaultMap?: Input_KeyMapper,
    applyKeyConfig?: () => void,
    readKeyConfig?: (config: object, key: string) => Input_KeyMapper,
    // QInput:
    keys?: {[a in _QInput_Action]: string|string[]},
};

type PluginManager_PluginDef = {
    name: string,
    status: boolean,
    description?: string,
    parameters: Record<string, string>,
    _filename?: string, // Added by RpgCommon, not available in plugins-setup event
};

declare var PluginManager: {
    setup(plugins: PluginManager_PluginDef[]): void,
    setParameters(name: string, parameters: PluginManager_PluginDef['parameters']): void;
    loadScript(filename: string): void;
    _scripts: string[],
};

// ------------------------------------------------------------------
// Other Managers
declare var SceneManager: {
    run(sceneClass: any): void,
};

// StorageManager global shadows DOM API, can't declare conflicting global
type _StorageManager = {
    localFileDirectoryPath(): string;
};

declare var DataManager: {
    loadDataFile(name: string, src: string): void;
    onLoad(object: object): void;
};

// ------------------------------------------------------------------
// Utils
interface UtilsCommon {
    RPGMAKER_NAME: "MV"|"MZ";
    RPGMAKER_VERSION: string;
    isOptionValid(name: string): boolean;
    isNwjs(): boolean;
    isMobileDevice(): boolean;
    isMobileSafari(): boolean;
    isAndroidChrome(): boolean;
}

interface UtilsMV extends UtilsCommon {
    RPGMAKER_NAME: "MV";
    canReadGameFiles?(): boolean,
    rgbToCssColor(r: number, g: number, b: number): string,
    generateRuntimeId(): number,
    isSupportPassiveEvent(): boolean,
}

interface UtilsMZ extends UtilsCommon {
    RPGMAKER_NAME: "MZ",
    checkRMVersion?(version: string): boolean,
    canUseWebGL(): boolean,
    canUseWebAudio(): boolean,
    canUseCssFontLoading(): boolean,
    canUseIndexedDB(): boolean,
    canPlayOgg(): boolean,
    canPlayWebm(): boolean,
    encodeURI(str: string): string,
    extractFileName?(filename: string): string,
    escapeHtml(str: string): string,
    containsArabic(str: string): boolean,
    setEncryptionInfo(hasImages: boolean, hasAudio: boolean, key: string): void,
    hasEncryptedImages(): boolean,
    hasEncryptedAudio(): boolean,
    decryptArrayBuffer(source: ArrayBuffer): ArrayBuffer,
}

declare var Utils: UtilsMV | UtilsMZ;

// ------------------------------------------------------------------
// Data
declare var $dataSystem: {
    variables: string[],
    switches: string[],
};

declare var $gameSwitches: {
    _data: boolean[],
};
declare var $gameVariables: {
    _data: any[],
};

// ------------------------------------------------------------------
// Game logic
declare var Game_Troop: {
    prototype: {
        setup(...args: any[]): any,
    },
};


// ==================================================================
// Plugin-specific globals
// See also above for monkey-patches on core types
declare var Imported: Record<string, any>|undefined;

// ------------------------------------------------------------------
// Yanfly plugins
declare var Yanfly: undefined|{
    Param: {
        BCEList: number[],
    },
};

// ------------------------------------------------------------------
// QInput plugin
type _QInput_Action = Input_Action|'fps'|'streched'|'fullscreen'|'restart'|'console';

declare var QInput: undefined|{
    remapped: {[k in _QInput_Action]: string},
    keys: {[k: number]: string},
};
