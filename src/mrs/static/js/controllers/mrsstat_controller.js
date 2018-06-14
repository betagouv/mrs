import { Controller } from 'stimulus'
import c3 from 'c3'

export default class extends Controller {
  connect() {
    var chartoptions = JSON.parse(this.element.innerHTML)
    c3.generate(chartoptions)
  }
}
