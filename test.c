#include "stdio.h"
#include "stdlib.h"


int solve()
{
   int n_bags, n_kids, *bags;
   scanf("%d %d\n", &n_bags, &n_kids);
   printf("%d %d\n", n_bags, n_kids);

   bags = (int*) malloc(n_bags * sizeof(int));
   scanf("%[^\n]%*d\n", bags);
   printf("%*d\n", *bags);

   return n_bags;
}

int main(int argc, char const *argv[])
{
   int n_cases; scanf("%d", &n_cases);
   int n_case = 1;

   for(; n_case <= n_cases; n_case ++) {
     	printf("Case #%d: %d\n", n_case, solve());
   };
}