/*
 * File: frida_native_function.js
 * Author: PiracyTools
 */

/*
 * Reference: https://pastebin.com/TVJD63uM
 * Use: frida -U -l "frida_native_function.js" -f $TARGET_PACKAGE_NAME
 */

setTimeout(function () {
    console.log("---");
    console.log("Capturing Android app...");
    if (Java.available) {
        console.log("[+] Java available");
        let nativeLibrary;
        for (const library of Process.enumerateModules()) {
            if (library["path"].includes("{NATIVE_LIBRARY_NAME}")) {
                nativeLibrary = library;
                break;
            }
        }

        if (nativeLibrary) {
            let exist = false;
            console.log("[*] Native library found");
            for (const module of nativeLibrary.enumerateExports()) {
                if (module["name"].includes("{NATIVE_MODULE_NAME}")) {
                    exist = true;
                    console.log(`[+] ${nativeModule["name"]} called - onEnter`);
                    Interceptor.attach(module["address"], {
                        onEnter: function (args) {
                            for (let i = 0; i < {NATIVE_ARGS_COUNT}; i++) {
                                console.log(`  --> [${i}] Raw value: ${args[i]}`);
                                console.log(`  --> [${i}] String value: ${Memory.readCString(args[i])}`);
                            }
                        },
                        onLeave: function(retval) {
                            console.log(`[-] ${nativeModule["name"]} called - onLeave`); 
                        }
                    });
                }
            }
            if (!exist) {
                console.log("[!] Native module not found");
            }
        } else {
            console.log("[!] Native library not found");
        }
    } else {
        console.log("[!] Java unavailable");
    }
    console.log("Capturing setup completed");
    console.log("---");
}, 0);