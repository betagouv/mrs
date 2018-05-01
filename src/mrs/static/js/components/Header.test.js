import React from 'react'
import {shallow} from 'enzyme'

import HeaderSmart, {
  Burger,
  CnamLogo,
  Header,
  HeaderFat,
  // HeaderMobile,
  Link,
  MenuLinks,
  MrsLogo,
} from './Header'

import * as UI from './UI.js'

describe('<Link />', () => {
  test('maps props correctly', () => {
    const alias = 'foo'
    const key = 1
    const url = 'url'
    const header = shallow(<Link
      alias={ alias }
      url={ url }
      key={ key } />)

    const subject = header.find('a')
    expect(subject.contains(alias)).toBeTruthy()
    expect(subject.props().className).toBe('link')
    expect(subject.props().href).toBe(url)
  })
})

describe('<MenuLinks />', () => {
  test('maps isOpened with correct className', () => {
    const isOpened = true
    const links = []
    const menuLinks1 = shallow(<MenuLinks
      links={ links }
      isOpened={ isOpened } />)
    const menuLinks2 = shallow(<MenuLinks links={ links } isOpened={ false }/>)

    const subject1 = menuLinks1.find('div')
    const subject2 = menuLinks2.find('div')

    expect(subject1.props().className).toBe('menu-links--wrapper')
    expect(subject2.props().className).toBe('menu-links--wrapper hidden')
  })

  test('maps links correctly', () => {
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
    ]

    const menuLinks = shallow(<MenuLinks
      links={ links } />)

    const subject1 = menuLinks.find(Link).at(0)
    const subject2 = menuLinks.find(Link).at(1)
    const subject3 = menuLinks.find(Link).at(2)

    expect(subject1.props().key).toBe(0)
    expect(subject2.props().key).toBe(1)
    expect(subject3.props().key).toBe(2)

    expect(subject1.props().url).toBe(links[0].url)
    expect(subject2.props().url).toBe(links[1].url)
    expect(subject3.props().url).toBe(links[2].url)

    expect(subject1.props().alias).toBe(links[0].alias)
    expect(subject2.props().alias).toBe(links[1].alias)
    expect(subject3.props().alias).toBe(links[2].alias)
  })
})

describe('<Burger />', () => {
  test('renders images with proper classNames', () => {
    const isOpened1 = false
    const isOpened2 = true

    const burger1 = shallow(<Burger isMenuOpened={isOpened1} />)
    const burger2 = shallow(<Burger isMenuOpened={isOpened2} />)

    const subject1 = burger1.find('img').at(0)
    const subject2 = burger1.find('img').at(1)
    const subject3 = burger2.find('img').at(0)
    const subject4 = burger2.find('img').at(1)

    expect(subject1.props().className).toBe('burger')
    expect(subject2.props().className).toBe('burger close hidden')
    expect(subject3.props().className).toBe('burger hidden')
    expect(subject4.props().className).toBe('burger close')
  })

  test('renders with proper image urls', () => {
    const burger = shallow(<Burger />)

    const subject1 = burger.find('img').at(0)
    const subject2 = burger.find('img').at(1)

    expect(subject1.props().src).toBe('/static/img/icones/burger.png')
    expect(subject2.props().src).toBe('/static/img/icones/croix.png')
  })

  test('renders with image alt texts', () => {
    const burger = shallow(<Burger />)

    const subject1 = burger.find('img').at(0)
    const subject2 = burger.find('img').at(1)

    expect(subject1.props().alt).toBe('menu')
    expect(subject2.props().alt).toBe('fermer')
  })

  test('renders with wrapper props', () => {
    const toggleMenu = () => {}
    const burger = shallow(<Burger toggleMenu={ toggleMenu } />)

    const subject = burger.find('div')

    expect(subject.props().onClick).toBe(toggleMenu)
    expect(subject.props().className).toBe('burger--wrapper')
  })
})

describe('<MrsLogo />', () => {
  test('props.isHidden', () => {
    // const isFat = true
    const mrsLogo1 = shallow(<MrsLogo
      isHidden={ true } />)
    const mrsLogo2 = shallow(<MrsLogo
      isHidden={ false } />)

    const subject1 = mrsLogo1.find('div')
    const subject2 = mrsLogo2.find('div')

    expect(subject1.props().className).toBe('mrs-logo--wrapper hidden')
    expect(subject2.props().className).toBe('mrs-logo--wrapper')
  })

  test('img src and alt', () => {
    const mrsLogo = shallow(<MrsLogo />)

    const subject = mrsLogo.find('img')

    expect(subject.props().src).toBe('/static/img/logos/mrs.png')
    expect(subject.props().alt).toBe('mrs')
  })
})

describe('<CnamLogo />', () => {
  test('props.isHidden', () => {
    const cnamLogo1 = shallow(<CnamLogo
      isHidden={ true } />)
    const cnamLogo2 = shallow(<CnamLogo
      isHiddem={ false } />)

    const subject1 = cnamLogo1.find('img')
    const subject2 = cnamLogo2.find('img')

    expect(subject1.props().className).toBe('logo-cnam hidden')
    expect(subject2.props().className).toBe('logo-cnam')
  })

  test('img src and alt', () => {
    const mrsLogo = shallow(<CnamLogo />)

    const subject = mrsLogo.find('img')

    expect(subject.props().src).toBe('/static/img/logos/cnam.png')
    expect(subject.props().alt).toBe('cnam')
  })
})

describe('<HeaderFat />', () => {
  test('proper wrapper', () => {
    const headerFat = shallow(<HeaderFat />)

    const subject = headerFat.find(UI.Row)
    expect(subject.props().className).toBe('HeaderFat--wrapper')
  })

  test('renders MrsLogo with correct props', () => {
    const headerFat1 = shallow(<HeaderFat isFat={ true } />)
    const headerFat2 = shallow(<HeaderFat isFat={ false } />)

    const subject1 = headerFat1.find(MrsLogo)
    const subject2 = headerFat2.find(MrsLogo)

    expect(subject1.props().isHidden).toBe(false)
    expect(subject2.props().isHidden).toBe(true)
  })

  test('renders CnamLogo with correct props', () => {
    const headerFat1 = shallow(<HeaderFat isFat={ true } />)
    const headerFat2 = shallow(<HeaderFat isFat={ false } />)

    const subject1 = headerFat1.find(CnamLogo)
    const subject2 = headerFat2.find(CnamLogo)

    expect(subject1.props().isHidden).toBe(true)
    expect(subject2.props().isHidden).toBe(false)
  })

  test('renders MenuLinks with correct props', () => {
    const isOpened = true
    const links = []
    const headerFat = shallow(<HeaderFat
      isMenuOpened={ isOpened }
      links={ links } />)

    const subject = headerFat.find(MenuLinks)

    expect(subject.props().links).toBe(links)
    expect(subject.props().isOpened).toBe(isOpened)
  })

  test('renders Burger with correct props', () => {
    const isOpened = true
    const toggleMenu = () => {}

    const headerFat = shallow(<HeaderFat
      isMenuOpened={ isOpened }
      toggleMenu={ toggleMenu } />)

    const subject = headerFat.find(Burger)

    expect(subject.props().isMenuOpened).toBe(isOpened)
    expect(subject.props().toggleMenu).toBe(toggleMenu)
  })
})

describe('<Header />', () => {
  test('wrapper', () => {
    const header1 = shallow(<Header isFat={ true } />)
    const header2 = shallow(<Header isFat={ false } />)

    const subject1 = header1.find('div')
    const subject2 = header2.find('div')

    expect(subject1.props().className).toBe('Header--wrapper')
    expect(subject2.props().className).toBe('Header--wrapper thin')
  })

  test('HeaderFat', () => {
    const props = {
      isFat: true,
      isMenuOpened: false,
      links: [],
      toggleMenu: () => {},
    }

    const header = shallow(<Header { ...props } />)

    const subject = header.find(HeaderFat)

    expect(subject.props().isFat).toBe(props.isFat)
    expect(subject.props().isMenuOpened).toBe(props.isMenuOpened)
    expect(subject.props().links).toBe(props.links)
    expect(subject.props().toggleMenu).toBe(props.toggleMenu)
  })
})

describe('<HeaderSmart />', () => {
  test('renders with props', () => {
    const props = {
      isFat: true,
      links: [],
    }

    const headerSmart = shallow(<HeaderSmart { ...props } />)
    const subject1 = headerSmart.find(Header)
    expect(subject1.props().isFat).toBe(props.isFat)
    expect(subject1.props().links).toBe(props.links)
    expect(subject1.props().isMenuOpened).toBe(false)

    headerSmart.setState({isOpened: true})
    const subject2 = headerSmart.find(Header)
    expect(subject2.props().isMenuOpened).toBe(true)
  })

  test('toggleIsOpened', () => {
    const subject = new HeaderSmart()

    expect(subject.state.isOpened).toBe(false)
    subject.toggleIsOpened()
    expect(subject.state.isOpened).toBe(true)
  })
})
