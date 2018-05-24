#include <stdio.h> 
#include <stdlib.h>
struct ex {int s; int d; int c; int n;};
int cm (const void *A, const void *B){
	return	((struct ex *)A)->d - ((struct ex *)B)->d;
	}
int main (){
int i, j, n, m;
int const MAX = 100;
int ans[100] = {0};
struct ex a[MAX];

scanf("%d %d",&n, &m);
for (i=0;i < m;i++){
	scanf("%d %d %d", &a[i].s, &a[i].d, &a[i].c);
	a[i].n = i + 1;
	ans[a[i].d - 1] = m + 1;
	}

qsort(a,m,sizeof a[0], cm);
j = 0;
for (i=0;i<n;i++){
	if(ans[i] == m + 1){
		j++;
		continue;
		}
	int k;
	for(k = j; k < m ; k++){
		if (a[k].s <= i + 1 && a[k].c > 0 ){
			ans[i] = a[k].n;
			a[k].c--;
			break;
			}
		}
	
	}
//check
j = 0;
for (i=0;i<m;i++)
	j += a[i].c;

if (j > 0)
//if(0)
	printf("-1");
else
	for (i = 0; i<n; i++)
		printf("%i ",ans[i]);
printf("\n");
return 0;
}
