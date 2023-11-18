#include <stdio.h>
#include <string.h>

#define S 100
#define N 1000

int main(int argc, char *argv[]) {
  char out[S];
  char buf[N] = {0};
  char msg[] = "Welcome to the argument echoing program\n";
  int len = 0;
  printf("%s", msg);
  for (int i = argc - 1; i > 0; --i) {
    len = snprintf(out, S, "argument %d is %s\n", i, argv[i]);
    if (len > 0 && len < N - strlen(buf)) {
      strncat(buf, out, len);
    }
  }
  printf("%s", buf);
  return 0;
}
