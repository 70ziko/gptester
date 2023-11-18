#include <stdio.h>
#include <stdlib.h>
 
enum { BUFFER_SIZE = 10 };
 
int main() {
    char buffer[BUFFER_SIZE];
    int check = 0;
 
    snprintf(buffer, sizeof(buffer), "%s", "This string is too long!");
 
    printf("check: %d\n", check); // This will correctly print 0 now
 
    return EXIT_SUCCESS;
}
