#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct exam{
	int a;
	int b;
	int c;
};

struct exam x[100];
int s[100],day[100]={0};

int compare(const void *a,const void *b){
	return x[*(int *)a].b-x[*(int *)b].b;
}

int main(void){
	int n,m,i,j;

	scanf("%d %d",&n,&m);
	for(i=0;i<m;i++){
		scanf("%d %d %d",&x[i].a,&x[i].b,&x[i].c);
		s[i]=i;
		day[x[i].b-1]=i+1;
	}

	qsort(s,m,sizeof(int),compare);

	for(i=0;i<n;i++){
		if(day[i]!=0){
			if(x[day[i]-1].c>0){
				printf("-1\n");
				return 0;
			}
			else{
				day[i]=m+1;
			}
		}
		else{
			for(j=0;j<m;j++){
				if(i+1>=x[s[j]].a&&x[s[j]].c>0){
					x[s[j]].c--;
					day[i]=s[j]+1;
					break;
				}
			}
		}
	}

	for(i=0;i<n-1;i++){
		printf("%d ",day[i]);
	}
	printf("%d\n",day[n-1]);

	return 0;
}
