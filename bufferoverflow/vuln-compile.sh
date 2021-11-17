gcc -ggdb vuln.c -o vuln -fno-stack-protector -z execstack
gcc caf.c -o caf -fno-stack-protector -z execstack -no-pie
