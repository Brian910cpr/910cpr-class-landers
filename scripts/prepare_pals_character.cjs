// Local, deterministic assembly from the owner's original bubble and edited baby.
// Uses the bundled Sharp runtime; no new artwork is generated.
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');
const repo = process.argv[2] || path.resolve(__dirname, '..');
const sourceDir=path.join(repo,'CUSTOMER_images','approved-course-characters');
async function component(file,seedX,seedY) {
 const {data,info:{width:w,height:h}}=await sharp(file).ensureAlpha().raw().toBuffer({resolveWithObject:true});
 const mask=new Uint8Array(w*h),queue=[seedY*w+seedX]; mask[queue[0]]=1;
 for(let q=0;q<queue.length;q++) {
  const p=queue[q],x=p%w,y=Math.floor(p/w);
  for(const n of [x>0?p-1:-1,x+1<w?p+1:-1,y>0?p-w:-1,y+1<h?p+w:-1])
   if(n>=0&&!mask[n]&&data[n*4+3]>=220){mask[n]=1;queue.push(n);}
 }
 // Retain the connected opaque artwork, dropping detached and translucent matte
 // fringe. Feather inward by one pixel so no contaminated outside RGB is used.
 const out=Buffer.alloc(data.length);
 for(const p of queue) {
  const x=p%w,y=Math.floor(p/w); let count=0;
  for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++)
   if(x+dx>=0&&x+dx<w&&y+dy>=0&&y+dy<h)count+=mask[(y+dy)*w+x+dx];
  out[p*4]=data[p*4];out[p*4+1]=data[p*4+1];out[p*4+2]=data[p*4+2];out[p*4+3]=Math.round(255*count/9);
 }
 console.log(path.basename(file),'retained component pixels:',queue.length);
 return {data:out,w,h};
}
(async()=>{
 const baby=await component(path.join(sourceDir,'PALS-baby-edit-source.png'),400,600);
 const bubble=await component(path.join(sourceDir,'PALS-owner-original.png'),850,200);
 const shifted=Buffer.alloc(bubble.data.length);
 for(let y=30;y<bubble.h;y++)for(let x=25;x<bubble.w;x++) {
  const src=(y*bubble.w+x)*4,dst=((y-30)*bubble.w+x-25)*4;
  if(bubble.data[src+3])bubble.data.copy(shifted,dst,src,src+4);
 }
 const output=await sharp(baby.data,{raw:{width:baby.w,height:baby.h,channels:4}})
  .composite([{input:shifted,raw:{width:baby.w,height:baby.h,channels:4}}]).png().toBuffer();
 await fs.promises.writeFile(path.join(sourceDir,'PALS-1.png'),output);
 for(const width of [480,960]){
  const name=width===480?'PALS-1-480.webp':'PALS-1.webp';
  await sharp(output).resize({width,withoutEnlargement:true}).webp({quality:90,effort:6}).toFile(path.join(repo,'docs','images','characters',name));
 }
 console.log('Saved PALS-1.png and responsive 480/960 WebP images.');
})();
