#include "copy_space.h"
int main(void)
{
    const char text[] = "OK\n";
    cs_write(text, 3);
    return 42;
}
