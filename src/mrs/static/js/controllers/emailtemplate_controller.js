import { Controller } from 'stimulus'
import M from 'mrsmaterialize'

export default class extends Controller {
  change() {
    const template = this.emailtemplates[this.element.value]

    if (template === undefined) return

    document.getElementById('id_subject').value = template.subject
    document.querySelector('label[for=id_subject]').className += ' active'

    const body = document.getElementById('id_body')
    body.value = template.body
    M.textareaAutoResize(body)
    document.querySelector('label[for=id_body]').className += ' active'
  }

  get emailtemplates() {
    return JSON.parse(document.getElementById('emailtemplates').innerHTML)
  }
}
