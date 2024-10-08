<template>
    <nav class="navbar">
        <div class="title"> <RouterLink to="/overview">價格追蹤小幫手</RouterLink></div>
        <ul class="options" v-show="isMobile ? isShow : true">
            <li><RouterLink to="/overview">物價概覽</RouterLink></li>
            <li><RouterLink to="/trending">物價趨勢</RouterLink></li>
            <li><RouterLink to="/news">相關新聞</RouterLink></li>
            <li v-if="!isLoggedIn"><RouterLink to="/login">登入</RouterLink></li>
            <li v-else @click="logout">Hi, {{getUserName}}! 登出</li>
        </ul>
        <div class="hamburger" @click="toggleMenu">☰</div>
    </nav>
</template>

<script>
import { useAuthStore } from '@/stores/auth';

export default {
    name: 'NavBar',
    data(){
        return{
            isShow: false,
            isMobile: false
        };
    },
    computed: {
        isLoggedIn(){
            const userStore = useAuthStore();
            return userStore.isLoggedIn;
        },
        getUserName(){
            const userStore = useAuthStore();
            return userStore.getUserName;
        }
    },
    methods: {
        logout(){
            const userStore = useAuthStore();
            userStore.logout();
        },
        toggleMenu(){
            this.isShow=!this.isShow;
            this.$emit('toggle-menu', this.isShow);
        },
        checkScreenSize(){
            this.isMobile = window.innerWidth < 768;
        }
    },
    mounted(){
        this.checkScreenSize();
        window.addEventListener('resize', this.checkScreenSize);
    },
    beforeUnmount(){
        window.removeEventListener('resize', this.checkScreenSize);
    }
};
</script>

<style scoped>
.navbar {
    display: flex;
    justify-content: space-between;
    background-color: #f3f3f3;
    padding: 1.5em;
    height: 4.5em;
    width: 100%;
    align-items: center;
    box-shadow: 0 0 5px #000000;
}

.navbar ul {
    list-style: none;
    display: flex;
    justify-content: space-around;
}

.title{
    justify-content: start;
    align-items: flex-start;
    margin-left: 1em;
}

.title > a{
    font-size: 1.4em;
    font-weight: bold;
    color: #2c3e50 !important;
}

.navbar li {
    color: #575B5D;
    margin: 0 .5em;
    font-size: 1.2em;
}

.navbar li:hover{
    cursor: pointer;
    font-weight: bold;
}

.navbar a {
    text-decoration: none;
    color: #575B5D;
}

.hamburger{
    display: none;
    cursor: pointer;
    font-size: larger;
}

@media (max-width: 768px){
    .navbar{
        margin: 0%;
        padding: 0%;
    }

    .hamburger{
        display: block;
        margin-right: 1em;
    }

    .options{
        flex-direction: column;
        justify-content: center;
        position: absolute;
        top: 4.5em;
        width: 100%;
        padding: 0%;
        margin: 0%;
        background-color: #f3f3f3;
    }

    li{
        width: 100%;
        height: 2em;
        border-top: #837c7c solid;
        line-height: 2em;
        padding: 0%;
        margin: 0%;
    }
}
</style>