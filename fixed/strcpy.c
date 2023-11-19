char str1[10];
char str2[]="abcdefghijklmn";
strncpy(str1, str2, sizeof(str1) - 1);
str1[sizeof(str1) - 1] = '\0';
