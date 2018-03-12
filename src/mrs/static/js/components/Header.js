import { h, render, Component } from 'preact'
import * as UI from './UI'

const Link = props => {
    return (
        <a
          href={ props.url }
          className="link"
          key={ props.key }>
          { props.alias }
        </a>
    )
}
const MenuLinks = props => {
    const links = props.links
          .map((e, i) => <Link key={ i } url={ e.url } alias={ e.alias } />)

    const isOpened = props.isOpened ? "" : " hidden"
    return (
        <div className={ "menu-links--wrapper" + isOpened }>
          { links }
        </div>
    )
}

MenuLinks.defaultProps = {
    links: [],
}

const HeaderFat = props => {
    const links = [
        {
            url: '/',
            alias: 'fonctionnement',
        },
        {
            url: '/foo',
            alias: 'formulaire',
        },
        {
            url: '/bar',
            alias: 'faq',
        },
        {
            url: '/bar',
            alias: 'contact',
        },
    ]

    return (
        <UI.Row>
          <div className="mrs-logo--wrapper">
            <img
                src="/static/img/logos/mrs.png"
                alt="mrs"
                className="logo-mrs" />
          </div>
          <MenuLinks
            links={ links }
            isOpened={ props.isMenuOpened } />
          <div
            onClick={ props.toggleMenu }
            className="burger--wrapper">
            <img
                src="/static/img/icones/burger.png"
                alt="menu"
                className={ "burger" + (!props.isMenuOpened ? "" : " hidden") } />
            <img
              src="/static/img/icones/croix.png"
              alt="femer"
              className={ "burger close " + (props.isMenuOpened ? "" : " hidden") } />
          </div>
        </UI.Row>
    )
}

const Header = props => {
    return (
        <div className="Header--wrapper">
          <HeaderFat { ...props } />
        </div>
    )
}

class HeaderSmart extends Component {
    constructor(props) {
        super(props)
        this.state = {
            isOpened: false,
        }

        this.toggleIsOpened = this.toggleIsOpened.bind(this)
    }

    toggleIsOpened() {
        this.setState({ isOpened: !this.state.isOpened })
    }

    render() {
        return <Header
            toggleMenu={ this.toggleIsOpened }
            isMenuOpened={ this.state.isOpened } />
    }

}

export default HeaderSmart
export {
    HeaderFat,
}
