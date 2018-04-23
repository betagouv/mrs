/* global M */
import { h as React, Component } from 'preact'

const CarouselSlide = props => {
  return (
    <div className="carousel-item">
      { props.children }
    </div>
  )
}

const CarouselUI = props => {
  return (
    <div className="CarouselDumb--wrapper">
      <div className="arrow--wrapper prev-slide">
        <img
          src="/static/img/icones/arrow.png"
          onClick={ props.prevSlide }
          alt="precedent"
          className="prev-slide-arrow" />
      </div>
      <div className="arrow--wrapper next-slide">
        <img
          src="/static/img/icones/arrow.png"
          onClick={ props.nextSlide }
          alt="suivant"
          className="next-slide-arrow" />
      </div>
      { props.children }
    </div>
  )
}

const CitationSlide = props => {
  return (
    <CarouselSlide>
      <div className="citation">{ props.citation }</div>
      <div className="author">{ props.author }</div>
    </CarouselSlide>
  )
}

CitationSlide.defaultProps = {
  citation: 'citation',
  author: 'author',
}

const CarouselDumb = props => {
  const slides = props.slides.map((e, i) =>
    <CitationSlide
      key={ i }
      author={ e.author }
      citation={ e.citation } />)

  return (
    <CarouselUI { ...props }>
      <div className="carousel carousel-slider">
        { slides }
      </div>
    </CarouselUI>
  )
}

CarouselDumb.defaultProps = {
  slides: [],
  pervSlide: () => {},
  nextSlide: () => {},
}

class Carousel extends Component {
  constructor(props) {
    super(props)

    this.state = {
      instance: {
        next: () => {},
        prev: () => {},
      },
    }

    this.nextSlide = this.nextSlide.bind(this)
    this.prevSlide = this.prevSlide.bind(this)
    this.startTimer = this.startTimer.bind(this)
  }

  componentDidMount() {
    const elem = document.querySelector('.carousel')
    const options = {
      dist: 0,
      indicators: true,
      fullWidth: true,
    }

    const instance = M.Carousel.init(elem, options)
    this.startTimer(instance)

    this.setState({ instance })
  }

  startTimer(instance) {
    this.timer = setInterval(() => instance.next(), 5000)
  }

  componentWillUnmount() {
    // destroy swiper instance
    this.state.instance.destroy()

    // stop timer
    clearInterval(this.timer)
  }

  nextSlide() {
    return this.state.instance.next.bind(this.state.instance)
  }

  prevSlide() {
    return this.state.instance.prev.bind(this.state.instance)
  }

  render() {
    return (
      <div className="carousel--wrapper">
        <CarouselDumb
          slides={ this.props.slides }
          prevSlide={ this.prevSlide() }
          nextSlide={ this.nextSlide() } />
      </div>
    )
  }
}

Carousel.defaultProps = {
  slides: [
    {
      citation: 'Bonjour, j’ai bien reçu le remboursement pour mes frais de transport en voiture particulière, paiement très rapide et simplifié grâce à l’envoi par internet! Merci !',
      author: 'Amelie F.',
    },
    {
      citation: '...sympa. Je reste à votre disposition et très belle initiative que la vôtre',
      author: 'Jean-Marie P.',
    },
    {
      citation: 'J’ai eu le plaisir de faire partie des premièrs patients à être remboursés grâce à ce système. Ce fut très rapide donc fort appréciable ! En espérant que bientôt tous les moyens transports soient également remboursés grâce à ce système. Merci pour les patients de mettre en place ce genre d’initiative',
      author: 'Maurice D. ',
    },
  ]
}

export default Carousel

export {
  CarouselDumb,
  CarouselSlide,
  CitationSlide,
  CarouselUI,
}
