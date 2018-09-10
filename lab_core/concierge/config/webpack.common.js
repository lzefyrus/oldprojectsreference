var webpack = require('webpack');
var HtmlWebpackPlugin = require('html-webpack-plugin');
var ExtractTextPlugin = require('extract-text-webpack-plugin');
var helpers = require('./helpers');

var config = {
  entry: {
    'app': './app/main.js'
  },

  resolve: {
    extensions: ['', '.js', '.ts'],
    alias: {
        jquery: "./jquery-2.1.1.js",
        hammerjs: "./hammer.min.js"
    }
  },
 externals: {
    jquery: 'jQuery'
  },
  module: {
    loaders: [
         {
            test: /\.jsx?$/,
            exclude: /node_modules/,
            loader: 'babel',

            query: {
               presets: ['es2015', 'react']
            }
         },
      {
        test: /\.html$/,
        loader: 'html'
      },
      {
        test: /\.(png|jpe?g|gif|svg|woff|woff2|ttf|eot|ico)$/,
        loader: 'file?name=static/concierge/app/assets/[name].[hash].[ext]'
      },
      {
        test: /\.css$/,

        loader: ExtractTextPlugin.extract('css', 'css?sourceMap')
      },
      {
        test: /\.css$/,
        include: helpers.root('app', 'app'),
        loader: 'raw'
      }
    ]
  },

  plugins: [
    new webpack.optimize.CommonsChunkPlugin({
      name: ['app']
    }),
    new webpack.ProvidePlugin({
      jQuery: 'jquery',
      $: 'jquery',
      jquery: 'jquery',
      createDayLabel: "jquery",
      createWeekdayLabel: "jquery"
    })
  ]
};

module.exports = config;