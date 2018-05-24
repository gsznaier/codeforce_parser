#include<stdio.h>
#include<stdlib.h>
int n,m;
int s[107],d[107],c[107];
int ix[107];
int r[107];
int slt(const void *p,const void *q){
	return d[*((int *)p)]-d[*((int *)q)];
}
void run(){
	int i,j,k;
	while(scanf("%d%d",&n,&m)!=EOF){
		for(i=0;i<m;i++){
			scanf("%d%d%d",&s[i],&d[i],&c[i]);
			s[i]--;
			d[i]--;
		}
		for(i=0;i<m;i++){
			ix[i]=i;
		}
		qsort(ix,m,sizeof(ix[0]),slt);
		for(i=0;i<n;i++){
			r[i]=0;
		}
		for(i=0;i<m;i++){
			r[d[i]]=m+1;
		}
		for(i=0;i<m;i++){
			k=0;
			for(j=s[ix[i]];j<d[ix[i]];j++){
				if(r[j]!=0){
					continue;
				}
				k++;
				r[j]=ix[i]+1;
				if(k==c[ix[i]]){
					break;
				}
			}
			if(k<c[ix[i]]){
				printf("-1\n");
				break;
			}
		}
		if(i<m){
			continue;
		}
		for(i=0;i<n;i++){
			printf("%d ",r[i]);
		}
		printf("\n");
	}
}
main(){
	run();
	return 0;
}
