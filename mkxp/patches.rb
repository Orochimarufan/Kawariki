# Kawariki MKXP patch/port collection
# See preload.rb for Patch implementation

module Preload
    Patches = [
        # Ports
        Patch.new("Zeus Fullscreen: Use mkxp builtin fullscreen instead (Alt+Enter)")
            .imported?(:Zeus_Fullscreen)
            .replace!("Zeus_Fullscreen++.rb"),
        Patch.new("HimeWorks' Event Trigger Labels: Fix any_key_pressed? implementation")
            .imported?(:TH_EventTriggerLabels)
            .replace!("TH_EventTriggerLabels.rb"),
        Patch.new("HimeWorks' Simple Audio Encryption: Re-Implement with direct path detection")
            .imported?(:TH_SimpleAudioEncryption)
            .replace!("TH_SimpleAudioEncryption.rb"),
        Patch.new("Super simple mouse script: Use mkxp mouse API")
            .imported?(nil)
            .include?("SUPER SIMPLE MOUSE SCRIPT")
            .replace!("Mouse.rb"),
        Patch.new("RMXP CustomResolution plugin")
            .imported?(nil)
            .include?("def snapshot(filename = 'Data/snap', quality = 0)")
            .replace!("XP_CustomResolution.rb"),
        Patch.new("Glitchfinder's Key Input: Shim with MKXP builtins")
            .imported?(nil)
            .include?("unless method_defined?(:keyinputmodule_input_update)")
            .replace!("Glitchfinder_Keyboard_Stub.rb"),
        Patch.new("Auto Font Install: Already included in MKXP")
            .imported?(nil)
            .include?("# ** Auto Font Install")
            .remove!,
        Patch.new("Extended Music Script: MKXP already supports .mod. other formats aren't available.")
            .imported?(nil)
            .include?("# Extended Music Script Version 3.5")
            .then!{|script|
                return if script.context.flag? :incompatible_bgm_checked
                unsupp = "wma,psf,minipsf,psf2,minipsf2,gsf,minigsf,usf,miniusf,hps,dsp,spc,gym,cym".split(",")
                # TODO: Find unsupported files in Audio/BGM. Then show msgbox if no converted versions available
                # Official MKXP-Z also doesn't support mp3
                script.context.mark :incompatible_bgm_checked
            }
            .remove!,
        # Specific Inline Patches
        Patch.new("Try to fix superclass mismatches from MP Scene_Base")
            .imported?(nil)
            .include?("======\nMoonpearl's Scene_Base\n-----")
            .flag!(:redefinitions_overwrite_class),
        # Generic Inline Patches
        Patch.new("Disable all font effects")
            .flag?(:no_font_effects) # KAWARIKI_MKXP_NO_FONT_EFFECTS
            .match?(/(\.f|F)ont\.(default_)?(italic|outline|shadow|bold)/)
            # Font is a built-in API, so it's already available in preload
            .then!{Font.default_italic = Font.default_outline = Font.default_shadow = Font.default_bold = false}
            .sub!(/Font\.default_(italic|outline|shadow|bold)\s*=/, "Font.default_\\1 = false &&")
            .sub!(/\.font\.(italic|outline|shadow|bold)\s*\=/, ".font.\\1 = false &&"),
        Patch.new("Improve Ruby 1.8 Compatibility")
            .if?{|script| script.context[:rgss_version] < 3} # Never on VX Ace, which shipped 1.9
            .match?("self.type", /\Wtype\.to_s\W/, /\Winstance_methods\.include\?\(['"%]/)
            .then!{require "ruby18.rb"},
    ]
end
