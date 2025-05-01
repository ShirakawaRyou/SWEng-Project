<template>
    <div>
      <p>{{ message }}</p>
    </div>
  </template>
   
  <script>
  import axios from 'axios'
   
  export default {
    data() {
      return {
        message: ''
      }
    },
    mounted() {
      this.fetchData()
    },
    methods: {
      async fetchData() {
        try {
          const response = await axios.get('http://127.0.0.1:8000/api/data/')
          this.message = response.data.message
        } catch (error) {
          console.error('Error fetching data:', error)
        }
      }
    }
  }
  </script>