/*
 * File: frida_function.js
 * Author: PiracyTools
 */

/*
 * Reference: https://stackoverflow.com/questions/65965281/code-for-frida-to-intercept-what-are-the-values-of-arguments-passing-through-the
 * Use: frida -U -D -l "frida_function.js" -f $TARGET_PACKAGE_NAME
 */


setTimeout(function () {
    console.log("---");
    console.log("Capturing Android app...");
    if (Java.available) {
        console.log("[+] Java available");
        let group;
        for (const method of Java.enumerateMethods("*{FUNCTION_CLASS_NAME}*!*")) {
            for (const item of method["classes"]) {
                if (item["methods"].includes("{FUNCTION_NAME}")) {
                    group = item["name"];
                    break;
                }
            }
        }

        if (group) {
            console.log("[+] Group found");
            Java.perform(function () {
                Java.use(group).{FUNCTION_NAME}.overload({FUNCTION_ARGS_TYPE}).implementation = function ({FUNCTION_ARGS}) {
{FUNCTION_CONSOLE_ARGS}
                    return this.{FUNCTION_NAME}({FUNCTION_ARGS});
                }
            });
        } else {
            console.log("[!] Group not found");
        }
    } else {
        console.log("[!] Java unavailable");
    }
    console.log("Capturing setup completed");
    console.log("---");
}, 0);