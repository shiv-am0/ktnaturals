document.documentElement.classList.add('js');
const toggle=document.querySelector('.menu-toggle');
const nav=document.querySelector('#public-nav');
if(toggle&&nav){
  toggle.addEventListener('click',()=>{
    const open=toggle.getAttribute('aria-expanded')!=='true';
    toggle.setAttribute('aria-expanded',String(open));
    nav.classList.toggle('is-open',open);
  });
  document.addEventListener('keydown',event=>{
    if(event.key==='Escape'&&toggle.getAttribute('aria-expanded')==='true'){
      toggle.setAttribute('aria-expanded','false');nav.classList.remove('is-open');toggle.focus();
    }
  });
}
const variant=document.querySelector('#variant');
if(variant){variant.addEventListener('change',()=>{
  const price=document.querySelector('.product-info .price');
  if(price)price.textContent=variant.selectedOptions[0].textContent;
});}
