import React, { Component } from 'react'
import * as UI from './UI'

const Link = props => {
  const isActive = window.location.pathname == props.url ? ' active' : ''
  return (
    <a
      href={ props.url }
      className={ 'link' + isActive }
      key={ props.key }>
      { props.alias }
    </a>
  )
}

const MenuLinks = props => {
  const links = props.links
    .map((e, i) => <Link key={ i } url={ e.url } alias={ e.alias } />)

  const isOpened = props.isOpened ? '' : ' hidden'
  return (
    <div className={ 'menu-links--wrapper' + isOpened }>
      { links }
    </div>
  )
}

MenuLinks.defaultProps = {
  links: [],
  isOpened: false,
}

const Burger = props => {
  return (
    <div
      onClick={ props.toggleMenu }
      className="burger--wrapper">
      <img
        src="/static/img/icones/burger.png"
        alt="menu"
        className={ 'burger' + (!props.isMenuOpened ? '' : ' hidden') } />
      <img
        src="/static/img/icones/croix.png"
        alt="fermer"
        className={ 'burger close' + (props.isMenuOpened ? '' : ' hidden') } />
    </div>
  )
}

const MrsLogo = props => {
  const wrapperClassName = 'mrs-logo--wrapper' + (props.isHidden ? ' hidden' : '')

  return (
    <div className={ wrapperClassName }>
      <img
        src="/static/img/logos/mrs.png"
        alt="mrs"
        className="logo-mrs" />
    </div>
  )
}

MrsLogo.defaultProps = {
  isHidden: false,
}

const CnamLogo = props => {
  const imgClassName = 'logo-cnam' + (props.isHidden ? ' hidden' : '')

  return (
    <div className="cnam-logo--wrapper">
      <img
        src="/static/img/logos/cnam.png"
        alt="cnam"
        className={ imgClassName } />
    </div>
  )
}

MrsLogo.defaultProps = {
  isHidden: false,
}


const HeaderFat = props => {
  return (
    <UI.Row className="HeaderFat--wrapper">
      <MrsLogo isHidden={ !props.isFat } />
      <CnamLogo isHidden={ props.isFat } />
      <MenuLinks
        links={ props.links }
        isOpened={ props.isMenuOpened } />
      <Burger
        isMenuOpened={ props.isMenuOpened }
        toggleMenu={ props.toggleMenu } />
    </UI.Row>
  )
}

const Header = props => {
  return (
    <div className={ 'Header--wrapper' + (props.isFat ? '' : ' thin') }>
      <HeaderFat { ...props } />
    </div>
  )
}

Header.defaultProps = {
  isFat: true,
  isMenuOpened: false,
  links: [],
  toggleMenu: () => {},
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
      isFat={ this.props.isFat }
      links={ this.props.links }
      toggleMenu={ this.toggleIsOpened }
      isMenuOpened={ this.state.isOpened } />
  }
}

HeaderSmart.defaultProps = {
  isFat: false,
  links: [
    {
      url: '/',
      alias: 'fonctionnement',
    },
    {
      url: '/demande',
      alias: 'formulaire',
    },
    {
      url: '/faq',
      alias: 'faq',
    },
    {
      url: '/contact',
      alias: 'contact',
    },
  ]
}

export default HeaderSmart
export {
  Burger,
  CnamLogo,
  Header,
  HeaderFat,
  Link,
  MenuLinks,
  MrsLogo,
}
