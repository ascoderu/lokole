module.exports = function(grunt) {

  grunt.loadNpmTasks('grunt-contrib-cssmin');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-bower-concat');

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    bower_concat: {
      all: {
        dest: {
          js: 'build/all.js',
          css: 'build/all.css'
        }
      },
    },

    cssmin: {
      options: {
        shorthandCompacting: false,
        roundingPrecision: -1
      },
      target: {
        files: {
          'opwen_email_client/static/app.min.css': ['build/all.css']
        }
      }
    },

    uglify: {
      bower: {
        options: {
          mangle: true,
          compress: true
        },
        files: {
          'opwen_email_client/static/app.min.js': 'build/all.js'
        }
      }
    },

  });

  grunt.registerTask('buildbower', [
    'bower_concat',
    'cssmin',
    'uglify:bower'
  ]);

  grunt.registerTask('default', [
    'buildbower'
  ])
};
