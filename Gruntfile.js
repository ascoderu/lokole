module.exports = function(grunt) {

  grunt.loadNpmTasks('grunt-contrib-copy');

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    copy: {
      bower: {
        files: [
          {
            expand: true,
            flatten: true,
            src: ['bower_components/components-font-awesome/fonts/*'],
            dest: 'opwen_email_client/webapp/static/fonts/',
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
            dest: 'opwen_email_client/webapp/static/flags/4x3/'
          },
          {
            expand: true,
            flatten: true,
            src: [
              'bower_components/jquery/dist/jquery.min.js',
              'bower_components/bootstrap/dist/js/bootstrap.min.js',
              'bower_components/bootstrap-fileinput/js/fileinput.min.js',
              'bower_components/bootstrap3-wysihtml5-bower/dist/bootstrap3-wysihtml5.all.min.js',
            ],
            dest: 'opwen_email_client/webapp/static/js/'
          },
          {
            expand: true,
            flatten: true,
            src: [
              'bower_components/components-font-awesome/css/font-awesome.min.css',
              'bower_components/flag-icon-css/css/flag-icon.min.css',
              'bower_components/bootstrap/dist/css/bootstrap.min.css',
              'bower_components/bootstrap-fileinput/css/fileinput.min.css',
              'bower_components/bootstrap3-wysihtml5-bower/dist/bootstrap3-wysihtml5.min.css',
            ],
            dest: 'opwen_email_client/webapp/static/css/'
          },
        ]
      }
    },

  });

  grunt.registerTask('default', [
    'copy:bower',
  ])
};
