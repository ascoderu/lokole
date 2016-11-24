module.exports = function(grunt) {

  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-bower-concat');

  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),

    bower_concat: {
      all: {
        dest: {
          js: 'build/all.js',
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
    'uglify:bower'
  ]);

  grunt.registerTask('default', [
    'buildbower'
  ])
};
