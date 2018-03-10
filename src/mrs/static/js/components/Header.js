import { h, render } from 'preact'

const Header = props => {
    return (
        <div className="Header--wrapper">
          <span>Hello, world!</span>
          <button onClick={ e => alert("hi!") }>Click Me</button>
        </div>
    )
}

export default Header
