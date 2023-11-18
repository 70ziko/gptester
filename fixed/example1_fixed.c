#include <stdio.h>
#include <tchar.h>

int _tmain(int argc, _TCHAR* argv[])
{
	char name[64];
	printf("Enter your name: ");
	fgets(name, sizeof(name), stdin);
	Sanitize(name);
	printf("Welcome, %s!", name);
	return 0;
}
