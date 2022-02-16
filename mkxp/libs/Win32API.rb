=begin
Win32API emulation

MKXP-Z exposes an implementation of the Win32API module (called MiniFFI) by default.
However, this alias is only actually useful on Windows. Therefore, we replace it
with a pure-ruby version specifically implementing the most common imports.
Real native libraries can still be accessed through MiniFII.new (e.g. in ports)

Lambdas are used for implementations as they replicate Win32API's #call interface.
=end

# Don't expose MiniFFI as Win32API
Object.remove_const :Win32API

module Win32API
    module Kernel32
        GetPrivateProfileInt = ->(appname, keyname, default, filename) do
            Preload.require "PreloadIni.rb"
            s = Preload::Ini.readIniString filename, appname, keyname
            s.nil? ? default : s.to_i
        end
        GetPrivateProfileString = ->(appname, keyname, default, ret, size, filename) do
            Preload.require "PreloadIni.rb"
            if appname.nil? then
                res = Preload::Ini.readIniSections(filename).join("\0") + "\0"
            elsif keyname.nil? then
                res = Preload::Ini.readIniKeys(filename, appname).join("\0") + "\0"
            else
                s = Preload::Ini.readIniString filename, appname, keyname
                res = s.nil? ? (default.nil? ? "" : default) : s
            end
            # C-String dance
            size -= 1
            if res.size > size then
                res.slice!(size...)
                res[size-1] = "\0" if appname.nil? or keyname.nil?
            end
            ret[...res.size] = res
            ret[res.size] = "\0"
            res.size
        end
        WritePrivateProfileString = ->(appname, keyname, value, filename) do
            writeIniString filename, appname, keyname, value
        end
    end

    Libraries = {
        "kernel32" => {
            "GetPrivateProfileInt" => Kernel32::GetPrivateProfileInt,
            "GetPrivateProfileIntA" => Kernel32::GetPrivateProfileInt,
            "GetPrivateProfileString" => Kernel32::GetPrivateProfileString,
            "GetPrivateProfileStringA" => Kernel32::GetPrivateProfileString,
            "WritePrivateProfileString" => Kernel32::WritePrivateProfileString,
            "WritePrivateProfileStringA" => Kernel32::WritePrivateProfileString,
        },

        "steam_api.dll" => {
            # TODO: Forward to native steamapi?
            "SteamAPI_Init" => ->{1},
            "SteamAPI_Shutdown" => ->{},
        },
    }

    def self.new(dllname, func, *rest)
        lib = Libraries[dllname]
        unless lib.nil? then
            result = lib[func]
            return result unless result.nil?
        end
        Preload.print("Warning: Win32API not implemented: #{dllname}##{func}")
        return ->(*args){Preload.print "(STUB) #{dllname}##{func}: #{args}"}
    end
end
