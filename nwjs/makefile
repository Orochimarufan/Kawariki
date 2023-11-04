TSC=node_modules/.bin/tsc

.PHONY: all js clean
all: js

js: node_modules
	$(TSC) --build

node_modules: package.json
	pnpm install

clean:
	$(TSC) --build --clean
