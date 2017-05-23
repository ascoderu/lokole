module.exports = function(grunt) {

  grunt.loadNpmTasks('grunt-contrib-copy');
  grunt.loadNpmTasks('grunt-contrib-cssmin');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-bower-concat');

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    bower_concat: {
      options: {
        separator: ';'
      },
      all: {
        dest: {
          js: 'build/js/_bower.js',
          css: 'build/css/_bower.css'
        },
        mainFiles: {
          bootstrap: [
            'dist/css/bootstrap.css',
            'dist/js/bootstrap.js'
          ]
        },
        dependencies: {
          'bootstrap': 'jquery',
          'bootstrap-fileinput': 'bootstrap',
          'bootstrap3-wysihtml5': 'bootstrap'
        }
      }
    },

    copy: {
      bower: {
        files: [
          {
            expand: true,
            flatten: true,
            src: ['bower_components/components-font-awesome/fonts/*'],
            dest:'opwen_email_client/webapp/static/fonts/',
            filter: 'isFile'
          },
          {
            expand: true,
            flatten: true,
            src: [
              'bower_components/flag-icon-css/flags/4x3/ca.svg',
              'bower_components/flag-icon-css/flags/4x3/cd.svg',
              'bower_components/flag-icon-css/flags/4x3/pt.svg',
              'bower_components/flag-icon-css/flags/4x3/tz.svg',
              'bower_components/flag-icon-css/flags/4x3/fr.svg',
            ],
            dest:'opwen_email_client/webapp/static/flags/4x3/',
            filter: 'isFile'
          },
        ]
      }
    },

    cssmin: {
      options: {
        shorthandCompacting: false,
        roundingPrecision: -1
      },
      target: {
        files: {
          'opwen_email_client/webapp/static/css/app.min.css': [
            'build/css/_bower.css'
          ]
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
          'opwen_email_client/webapp/static/js/app.min.js': [
            'build/js/_bower.js'
          ]
        }
      }
    },

  });

  grunt.registerTask('buildbower', [
    'bower_concat',
    'copy:bower',
    'cssmin',
    'uglify:bower'
  ]);

  grunt.registerTask('default', [
    'buildbower'
  ])
};
