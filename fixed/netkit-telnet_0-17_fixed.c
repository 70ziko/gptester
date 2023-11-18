/*
netkit-telnet 0.17 BUFFER OVERFLOW
*/

#include <netdb.h>
#include <string.h>

static void env_fix_display(void) {
    enviro *ep = env_find("DISPLAY");
    if (!ep) return;
    ep->setexport(1);
    if (strncmp(ep->getval(), ":", 1) && strncmp(ep->getval(), "UNIX", 5)) {
        return;
    }
    char hbuf[256];
    const char *cp2 = strrchr(ep->getval(), ':');
    if (!cp2) return;
    int maxlen = sizeof(hbuf) - strlen(cp2) - 1;
    gethostname(hbuf, maxlen);
    hbuf[maxlen] = '\0';
    if (!strchr(hbuf, '.')) {
        struct hostent *h = gethostbyname(hbuf);
        if (h) {
            strncpy(hbuf, h->h_name, maxlen);
            hbuf[maxlen] = '\0';
        }
    }
    strncat(hbuf, cp2, sizeof(hbuf) - strlen(hbuf) - 1);
    ep->define("DISPLAY", hbuf);
}
