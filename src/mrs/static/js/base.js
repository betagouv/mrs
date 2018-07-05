import ScrollReveal from 'scrollreveal'
import 'materialize-css/sass/materialize.scss'
import '../sass/base.sass'
import '../sass/landing.sass'
import '../sass/base.sass'
import '../sass/form.sass'
import '../sass/animations.sass'
import '../sass/index.sass'
import '../sass/faq.sass'
import '../sass/caroussel.sass'
import './mrsrequest'
import './contact'
import M from 'materialize-css'

// Preact imports
import { h as React, render } from 'preact'
import Header from './components/Header.js'
import Carousel from './components/Caroussel.js'


(() => {
  let body = document.querySelector('body')

  const renderHeader = isFat => render(<Header isFat={ isFat } />, document.getElementById('header'))
  const renderCarousel = () => render(<Carousel />, document.getElementById('caroussel'))

  // show correct header based on path
  if(body.classList.contains('index')) {
    const sr = ScrollReveal()
    sr.reveal('.scroll-reveal')
    renderHeader(false)
    renderCarousel()
  } else {
    renderHeader(true)
  }

  M.AutoInit()

  for (let form of body.querySelectorAll('form[data-autosubmit]')) {
    form.addEventListener('change', () => {
      form.submit()
      body.innerHTML = `
<div class="preloader-wrapper big active">
  <div class="spinner-layer spinner-blue">
    <div class="circle-clipper left">
      <div class="circle"></div>
    </div><div class="gap-patch">
      <div class="circle"></div>
    </div><div class="circle-clipper right">
      <div class="circle"></div>
    </div>
  </div>
</div>
      `
    })
    form.style.display = 'block'
  }
})()
