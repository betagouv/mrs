var path = require('path')
var BundleTracker = require('webpack-bundle-tracker')
const ExtractTextPlugin = require('extract-text-webpack-plugin')
const UglifyJSPlugin = require('uglifyjs-webpack-plugin')

const extractSass = new ExtractTextPlugin({
    filename: '[name].[hash].css',
})

var production = process.env.NODE_ENV == 'production'

var cfg = {
  context: __dirname,
  mode: production ? 'production' : 'development',

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
    crudlfap: [
      'babel-polyfill',
      'whatwg-fetch',
      './src/mrs/static/js/crudlfap',
      './node_modules/c3/c3.css',
      './node_modules/mrsmaterialize/sass/materialize.scss',
    ],
    mrsbootstrap: [
      './src/mrs/static/scss/mrs.scss',
    ],
    mrsindex: [
      'countup.js', './src/mrs/static/js/mrsindex',
    ],
    mrsfaq: [
      './src/mrs/static/js/mrsfaq',
    ],
  },
  output: {
    path: path.resolve('./src/mrs/static/webpack_bundles/'),
    filename: '[name].[hash].js',
    pathinfo: false
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
        exclude: /(turbolinks)/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['stage-2', 'babel-preset-env'],
            plugins: ['transform-es2015-arrow-functions'],
            sourceMap: true
          }
        }
      },
      {
        test: /\.s?(a|c)ss$/,
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
  },

  optimization: {
    removeAvailableModules: false,
    removeEmptyChunks: false,
    splitChunks: false,
  }
}

if (production) {
  cfg.plugins.push(new UglifyJSPlugin({
    sourceMap: true
  }))
}

module.exports = cfg
