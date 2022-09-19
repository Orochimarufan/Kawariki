# Kawariki MKXP preload infrastructure

module Preload
    # Kawariki mkxp resources location
    Path = File.dirname __FILE__

    # Require common libs
    def self.require(name)
        Kernel.require File.join(Path, "libs", name)
    end

    module Common
        # In RMXP mode, Kernel.print opens message boxes
        def print(text)
            STDOUT.puts("[preload] " + text)
        end
    end

    extend Common

    # -------------------------------------------------------------------------
    # Patches
    # -------------------------------------------------------------------------
    class Context
        include Common

        def initialize(scripts)
            @scripts = scripts
            @script_instances = {}
            @options = {}
            @blacklist = []
            @delay = {}
            @script_id_digits = Math.log10(scripts.size).ceil
        end

        attr_reader :script_id_digits, :script_loc_format

        # Scripts
        def script(i)
            @script_instances[i] ||= Script.new self, i, @scripts[i]
        end

        def script_count
            @scripts.size
        end

        def each_script
            (0...@scripts.size).each {|i| yield script i}
        end

        def script_loc(scriptid)
            return script(scriptid).loc
        end

        def blacklisted?(script)
            @blacklist.include? script.name
        end

        # Read options from environment
        FalseEnvValues = [nil, "", "0", "no"]
        def read_env(env=ENV)
            env_bool = ->(name) {!FalseEnvValues.include?(env[name])}
            env_str = ->(name) {e = env[name]; e unless e == ""}
            env_list = ->(name, delim) {e = env[name]; e.nil? ? [] :  e.split(delim)}

            set :dump_scripts_raw, env_str.("KAWARIKI_MKXP_DUMP_SCRIPTS")
            set :dump_scripts_patched, env_str.("KAWARIKI_MKXP_DUMP_PATCHED_SCRIPTS")
            mark :dont_run_game if env_bool.("KAWARIKI_MKXP_DRY_RUN")
            mark :no_font_effects if env_bool.("KAWARIKI_MKXP_NO_FONT_EFFECTS")
            @blacklist = env_list.("KAWARIKI_MKXP_FILTER_SCRIPTS", ",")
        end

        def read_system(system=System)
            # TODO: Non mkxp-z variants
            set :mkxp_version, system::VERSION
            set :mkxp_version_tuple, (system::VERSION.split ".").map{|d| d.to_i}

            if (self[:mkxp_version_tuple] <=> [2, 4]) >= 0 then
                mark :mkxpz_24
                _config = CFG
            else
                _config = system::CONFIG
            end
            set :rgss_version, _config["rgssVersion"].to_i

            # FIXME: can this be reliably retrieved from MKXP if set to 0 in config?
            if self[:rgss_version] == 0 then
                print "Warning: rgssVersion not set in MKXP config. Are you running mkxp directly?"
                if RGSS_VERSION == "3.0.1" then
                    # See mkxp-z/mri-binding.cpp
                    set :rgss_version, 3
                else
                    print "Warning: Cannot guess RGSS version. Kawariki should automatically set it correctly."
                end
            end
            if self[:mkxp_version] == "MKXPZ_VERSION" then
                print "Note: Using mkxp-z with broken System::VERSION reporting. Cannot detect real mkxp-z version"
                set :mkxp_version, "mkxp-z"
            end
        end

        # Options
        def set(sym, value=true)
            @options.store sym, value unless value.nil?
        end

        def [](sym)
            @options[sym]
        end

        def mark(*flags)
            flags.each{|flag| set flag, true}
        end

        def flag?(flag)
            @options.key? flag
        end

        # Delay
        DelaySlots = [:after_patches]

        def delay(slot, &p)
            raise "Unknown delay slot #{slot}" unless DelaySlots.include? slot
            @delay[slot] = [] unless @delay.key? slot
            @delay[slot].push p
        end

        def run_delay_slot(slot, *args)
            raise "Unknown delay slot #{slot}" unless DelaySlots.include? slot
            if @delay[slot] then
                @delay[slot].each {|p| p.call(self, *args)}
                @delay.delete slot
            end
        end
    end

    class Script
        def initialize(context, i, script)
            @context = context
            @index = i
            @script = script
            @log = []
        end

        attr_reader :context
        attr_reader :index

        def log(msg=nil)
            @log.push msg unless msg.nil? || @log.last == msg
            @log
        end

        def loc
            "##{index.to_s.rjust @context.script_id_digits} '#{name}'"
        end

        def [](i)
            @script[i]
        end

        def name
            @script[1]
        end

        def source
            @script[3]
        end

        def sub!(*p)
            @script[3].gsub!(*p)
        end

        def source=(code)
            @script[3] = code
        end

        def load_file(path)
            log "replaced with #{File.basename path}"
            @script[3] = File.read(path)
        end

        def remove
            log "removed"
            @script[3] = ""
        end

        # Extract $imported key only once
        ImportedKeyExpr = /^\s*\$imported\[(:\w+|'[^']+'|"[^"+]")\]\s*=\s*(.+)\s*$/

        def _extract_imported
            match = ImportedKeyExpr.match(source)
            @imported_entry = !match.nil?
            return unless @imported_entry
            @imported_key = match[1][0] == ':' ? match[1][1..].to_sym : match[1][1...-1]
            @imported_value = match[2]
        end

        def imported_entry?
            _extract_imported if @imported_entry.nil?
            @imported_entry
        end

        def imported_key
            _extract_imported if @imported_entry.nil?
            @imported_key
        end

        def imported_value
            _extract_imported if @imported_entry.nil?
            @imported_value
        end
    end

    class Patch
        include Common

        def initialize(desc=nil)
            @description = desc
            @conditions = []
            @actions = []
            @terminal = false
        end

        def is_applicable(script)
            return @conditions.all? {|cond| cond.call(script)}
        end

        def apply(script)
            print "Patch   #{script.loc}: #{@description}"
            @actions.each {|action| action.call script}
            @terminal
        end

        def eval(script)
            apply script if is_applicable script
        end

        # --- Conditions ---
        # Arbitrary condition
        def if?(&p)
            @conditions.push p
            self
        end

        # Source code contains text
        def include?(str)
            # XXX: maybe should restrict this to the start of the script for performance?
            if? {|script| script.source.include? str}
        end

        # Source code matches (any) pattern
        def match?(*ps)
            pattern = Regexp.union(*ps)
            if? {|script| script.source.match? pattern}
        end

        # Script sets $imported[key]
        def imported?(key)
            if? {|script| script.imported_key == key}
        end

        # Global flag set
        def flag?(flag)
            if? {|script| script.context.flag? flag}
        end

        # --- Actions ---
        # Arbitrary action
        def then!(&p)
            @actions.push p
            self
        end

        # Run arbitrary action later
        def delay!(slot, &p)
            @actions.push proc{|script|script.context.delay(slot, &p)}
            self
        end

        # Substitute text
        def sub!(pattern, replacement)
            @actions.push proc{|script| script.source.gsub! pattern, replacement}
            self
        end

        # Set a global flag for later reference
        def flag!(*flags)
            @actions.push proc{|script| script.context.mark *flags}
            self
        end

        # Remove the script (terminal)
        def remove!
            @actions.push proc{|script| script.remove }
            @terminal = true
            self
        end

        # Replace the whole script with a file from ports/ (terminal)
        def replace!(filename)
            @actions.push proc{|script| script.load_file File.join(Path, "ports", filename)}
            @terminal = true
            self
        end

        # Stop processing this script if patch is applicable (terminal)
        def next!
            @terminal = true
            self
        end
    end

    # -------------------------------------------------------------------------
    # Apply Patches
    # -------------------------------------------------------------------------
    class ClassInfo
        include Common

        def initialize(name, script, supername)
            @name = name
            @defs = [[script, supername]]
            @superdef = 0
        end

        attr_reader :name
        attr_reader :defs

        def first_script
            return @defs[0][0]
        end

        def super_name
            return @defs[@superdef][1]
        end

        def super_script
            return @defs[@superdef][0]
        end

        def first_loc
            return first_script.loc
        end

        def super_loc
            return super_script.loc
        end

        def add_definition(script, supername)
            if !supername.nil? && super_name != supername then
                print "Warning: Redefinition of class '#{name}' in #{script.loc} with inconsistent superclass '#{supername}'. Previous definition in #{super_loc} has superclass '#{super_name}'"
                @superdef = @defs.size
            end
            @defs.push [script, supername]
        end

        def inconsistent?
            return @superdef > 0
        end
    end

    def self.get_class_defs(ctx)
        classes = {}
        expr = /^class\s+(\w+)\s*(?:<\s*(\w+)\s*)?$/
        ctx.each_script do |script|
            # Encoding is all kinds of messed up in RM
            e = script.source.encoding
            script.source.force_encoding Encoding.find("ASCII-8BIT")
            script.source.scan(expr) do |groups|
                name, supername = *groups
                if !classes.include? name then
                    classes[name] = ClassInfo.new name, script, supername
                else
                    classes[name].add_definition script, supername
                end
            end
            script.source.force_encoding e
        end
        return classes
    end

    def self.overwrite_redefinitions(ctx)
        classes = get_class_defs ctx
        classes.each_pair do |name, cls|
            if cls.inconsistent? then
                print "Eliminating definitions of class '#{name}' before #{cls.super_loc}. First in #{cls.first_loc}"
                cls.super_script.sub!(Regexp.new("^(class\\s+#{name}\\s*<\\s*#{cls.super_name}\\s*)$"),
                    "Object.remove_const :#{name}\n\\1")
            end
        end
    end

    def self.patch_scripts(ctx)
        ctx.each_script do |script|
            # Remove blacklisted scripts
            if ctx.blacklisted? script then
                print "Removed #{script.loc}: Blacklisted"
                script.remove
                next
            end
            # Encodings are a mess in RGSS. Can break Regexp matching
            e = script.source.encoding
            script.source.force_encoding "ASCII-8BIT"
            # Apply patches
            Patches.each do |patch|
                break if patch.eval script
            end
            print "Patched #{script.loc}: #{script.log.join(', ')}" if script.log.size > 0
            # Warn if Win32API references in source
            if script.source.include? "Win32API.new" then
                print "Warning: Script #{script.loc} uses Win32API."
                require "Win32API.rb"
            end
            # Restore encoding
            script.source.force_encoding e
        end
        ctx.run_delay_slot :after_patches
    end

    NoFilenameChars = "/$|*#="

    def self.dump_scripts(ctx, opt)
        # Dump all scripts to a folder specified by opt
        if ctx.flag? opt then
            dump = ctx[opt]
            print "Dumping all scripts to %s" % dump
            Dir.mkdir dump unless Dir.exist? dump
            fn_format = "%0#{ctx.script_id_digits}d%s%s%s"
            ctx.each_script do |script|
                filename = fn_format % [script.index,
                                        script.name.empty? ? "" : " ",
                                        script.name.tr(NoFilenameChars, "_"),
                                        script.source.empty? ? "" : ".rb"]
                File.write File.join(dump, filename), script.source
            end
        end
    end

    RgssVersionNames = ["Unknown", "XP", "VX", "VX Ace"]

    def self.run
        # Initialize
        ctx = Context.new $RGSS_SCRIPTS
        ctx.read_system
        ctx.read_env
        print "MKXP mkxp-z #{ctx[:mkxp_version]} RGSS #{ctx[:rgss_version]} (#{RgssVersionNames[ctx[:rgss_version]]})\n"
        # Patch Scripts
        dump_scripts ctx, :dump_scripts_raw
        patch_scripts ctx
        overwrite_redefinitions ctx if ctx.flag? :redefinitions_overwrite_class
        dump_scripts ctx, :dump_scripts_patched
        # Done
        if ctx.flag? :dont_run_game then
            print "KAWARIKI_MKXP_DRY_RUN is set, not continuing to game code"
            exit 123
        end
    end
end

Kernel.require File.join(Preload::Path, 'patches.rb')
Preload.run
