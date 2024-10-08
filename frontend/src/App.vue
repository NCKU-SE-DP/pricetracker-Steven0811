<template>
  <NavBar class="navbar" @toggle-menu="onToggleMenu"></NavBar>
  <RouterView :class="isMenuOpen ? 'menuOpen' : 'render'"></RouterView>
</template>

<script>
// import { RouterView } from 'vue-router';
import NavBar from './components/NavBar.vue'
export default {
  name: 'App',
  components: {
    NavBar,
  },
  data(){
    return{
      isMenuOpen: false
    };
  },
  methods:{
    onToggleMenu(isShow){
      this.isMenuOpen = isShow;
    },
    checkScreenSize(){
      this.isMenuOpen = window.innerWidth < 768;
    }
  },
  mounted(){
    this.checkScreenSize();
    window.addEventListener('resize', this.checkScreenSize);
  },
  beforeUnmount(){
    window.removeEventListener('resize', this.checkScreenSize);
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}
.navbar{
  z-index: 1000;
  position: fixed;
  top: 0;
}
.render{
  margin-top: 4.5em;
  box-shadow: 0 0 2em #f3f3f3;
}
.menuOpen{
  margin-top: 14em;
}
</style>
