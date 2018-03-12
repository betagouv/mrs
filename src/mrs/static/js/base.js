import ScrollReveal from 'scrollreveal'
import '../sass/landing.sass'
import '../sass/base.sass'
import '../sass/form.sass'
import '../sass/animations.sass'
import './mrsrequest'
import initStatistics from './statistics.js'

// Preact imports
import { h, render } from 'preact'
import Header from './components/Header.js'


(($) => {
    let body = document.querySelector('body')

    // show correct header based on path
    if(body.classList.contains('index')) {
        const sr = ScrollReveal()
        sr.reveal('.scroll-reveal')

        $('body').on('click', '[data-callback=scroll-to]', function() {
            var $target = $($(this).attr('data-target'))

            $('html, body').animate({
                scrollTop: $target.offset().top + 'px'
            }, 'fast')
        })

        render(<Header />, document.getElementById('header'))
    }

    // use bodyclass to detect statistics
    if(body.classList.contains('statistics')) {
        initStatistics()
        render(<Header isFat={ true }/>, document.getElementById('header'))
    }

})(window.jQuery)
