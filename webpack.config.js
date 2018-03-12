var path = require('path')
var BundleTracker = require('webpack-bundle-tracker')
const ExtractTextPlugin = require('extract-text-webpack-plugin')

const extractSass = new ExtractTextPlugin({
    filename: '[name].[contenthash].css',
})

module.exports = {
  context: __dirname,

  /*
    pages:
      - index (/)
      - mrsrequest (/demande)
      - contact (/contact)
      - FAQ (/faq)
      - legal (/legal)
      - statistics (/stats)

    base.html:
      - header
      - footer
  */
  entry: {
    base: ['babel-polyfill', './src/mrs/static/js/base'],
    iframe: ['./src/mrs/static/js/iframe'],
    admin: ['./src/mrs/static/js/admin'],
  },
  output: {
    path: path.resolve('./src/mrs/static/webpack_bundles/'),
    filename: '[name]-[hash].js'
  },

  plugins: [
    new BundleTracker({filename: './webpack-stats.json'}),
    extractSass
  ],

  devtool: 'source-map',
  module: {
    rules: [
      {
        test: /\.js$/,
        //exclude: /(node_modules|bower_components)/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['stage-2', 'babel-preset-env']
          }
        }
      },
      {
        test: /\.sass$/,
        use: extractSass.extract({
          use: [{
            loader: 'css-loader', options: {
              sourceMap: true
            }
          }, {
            loader: 'sass-loader', options: {
              sourceMap: true
            }
          }]
        })
      }
    ]
  }
}
