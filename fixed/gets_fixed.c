#include <stdio.h>
int main () {
    char username[8];
    int allow = 0;
    printf("Enter your username, please: ");
    fgets(username, sizeof(username), stdin); // use fgets instead of gets to avoid buffer overflow
    if (grantAccess(username)) {
        allow = 1;
    }
    if (allow != 0) { 
        privilegedAction();
    }
    return 0;
}
