import { h as React, Component } from 'preact'

const CarouselSlide = props => {
    return (
        <div className="carousel-item">
          { props.children }
        </div>
    )
}

const CarouselDumb = props => {
    return (
        <div className="CarouselDumb--wrapper">
          <h3>Ils ont deja utilise notre service !</h3>
          <img
            src="/static/img/icones/open-quotes.png"
            alt="icone"
            class="quote-img" />
          <div className="arrow--wrapper prev-slide">
            <img
              src="/static/img/icones/arrow.png"
              onClick={ props.prevSlide }
              alt="precedent"
              class="prev-slide-arrow" />
          </div>
          <div className="arrow--wrapper next-slide">
            <img
              src="/static/img/icones/arrow.png"
              onClick={ props.nextSlide }
              alt="suivant"
              class="next-slide-arrow" />
            </div>
          <div className="carousel carousel-slider">
            <CarouselSlide>
              <div>TEST1</div>
            </CarouselSlide>

            <CarouselSlide>
              <div>TEST2</div>
            </CarouselSlide>

            <CarouselSlide>
              <div>TEST3</div>
            </CarouselSlide>
          </div>
        </div>
    )
}

CarouselDumb.defaultProps = {
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
    }

    componentDidMount() {
        const elem = document.querySelector('.carousel')
        const options = {
            dist: 0,
            indicators: true,
            fullWidth: true,
        }

        const instance = M.Carousel.init(elem, options)
        this.setState({ instance })
    }

    componentWillUnmount() {
        this.state.instance.destroy()
    }

    nextSlide() {
        return this.state.instance.next.bind(this.state.instance)
    }

    prevSlide() {
        return this.state.instance.prev.bind(this.state.instance)
    }

    render() {
        return (
            <div class="carousel--wrapper">
              <CarouselDumb
                prevSlide={ this.prevSlide() }
                nextSlide={ this.nextSlide() } />
            </div>
        )
    }
}

export default Carousel

export {
    CarouselDumb,
    CarouselSlide,
}
