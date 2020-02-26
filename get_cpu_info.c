#include <stdio.h>
void cpu_id(char *id)
{
    char s[17];
    unsigned   int   s1,s2;
    char   sel;
    asm volatile
    ( "movl $0x01 , %%eax ; \n\t"
    "xorl %%edx , %%edx ;\n\t"
    "cpuid ;\n\t"
    "movl %%edx ,%0 ;\n\t"
    "movl %%eax ,%1 ; \n\t"
    :"=m"(s1),"=m"(s2)
    );
    sprintf(s,"%08X%08X",s1,s2);
    for(int i=7;i>=0;i--)
    {
        id[2*(7-i)] = s[i*2];
        id[2*(7-i)+1] = s[i*2+1];
    }
    id[16] = '\0';
}
int   main(int   argc,   char*   argv[])
{
    char id[17];
    cpu_id(id);
    printf("%s\n",id);
    return   0;
}