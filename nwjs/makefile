TSC=node_modules/.bin/tsc

.PHONY: all js clean
all: js js/es5/s.js

js: node_modules
	$(TSC) --build

node_modules: package.json
	pnpm install

js/es5/s.js: node_modules node_modules/systemjs/dist/s.js
	cp node_modules/systemjs/dist/s.js $@

clean:
	$(TSC) --build --clean
