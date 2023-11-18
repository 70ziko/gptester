#include <stdio.h>
#include <stdlib.h>
 
enum { BUFFER_SIZE = 10 };
 
int main() {
    char buffer[BUFFER_SIZE];
    int check = 0;
 
    snprintf(buffer, BUFFER_SIZE, "%s", "This string is too long!");
 
    printf("check: %d", check); /* This will print 0 (safe version)*/
 
    return EXIT_SUCCESS;
}
