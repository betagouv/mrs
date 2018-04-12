// Add our controllers to crudlfap's

import { Application } from 'stimulus'
import { definitionsFromContext } from 'stimulus/webpack-helpers'
import M from 'materialize-css'
import 'crudlfap/js/style.sass'

(() => {
  var Turbolinks = require('turbolinks')
  Turbolinks.start()
}).bind(window)()

const application = Application.start()
var context = require.context('./controllers', true, /\.js$/)
application.load(definitionsFromContext(context))

context = require.context('crudlfap/js/controllers', true, /\.js$/)
application.load(definitionsFromContext(context))

// Manual controller teardown
// https://github.com/stimulusjs/stimulus/issues/104
document.addEventListener('turbolinks:before-render', function() {
  application.controllers.forEach(function(controller) {
    if(typeof controller.teardown === 'function') {
      controller.teardown()
    }
  })
})

document.addEventListener('turbolinks:load', function(e) {
  M.AutoInit(e.target.body)
})
