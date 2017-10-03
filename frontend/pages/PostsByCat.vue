<template>
  <div>
    <ad-component></ad-component>
    <Row>
      <Col :span="20">
        <h1>{{ catTitle }} quotes<span v-if="page > 0">, page {{ page }}</span></h1>
      </Col>
    </Row>
    <Row v-for="(chunk, index) in chunkPosts" :key="'p-' + index" style="background:#eee;padding:20px" class="posts-row">
      <Col :span="2"></Col>
      <Col :span="8" v-for="(post, i) in chunk" :key="index + i" class="posts-col">
        <Card :bordered="false">
          <div v-if="post.image">
            <a :href="baseUrl + post.slug + '/'"><img :src="imgBaseUrl + post.image" :alt="post.title" class="img-fluid"></a>
          </div>
          <div>
            <p><small>
            <a :href="baseUrl + keyword + '/' + post.category_id.Slug + '/'">{{ post.category_id.Title }} quotes</a>
            </small></p>
          </div>
          <div :style="bgColor()">
            <p v-if="post.content" v-html="post.content" style="color: white; padding: 25px"></p>
          </div>
        </Card>
      </Col>
      <Col :span="2"></Col>
      <Col :span="20" v-if="index === (3 || 7)">
        <ad-component></ad-component>
      </Col>
    </Row>
    <paginator-component v-once :totalPages="calcPages" :paginatorType="paginatorType" :value="catSlug" :currentPage="page" :itemsPerPage="itemsPerPage" :totalItems="posts[0].total_posts">
    </paginator-component>
  </div>
</template>

<script>
import chunk from '../plugins/chunk'
import Paginator from '../components/Paginator.vue'
import Ads from '../components/Ads.vue'
import axios from 'axios'

export default {
  data () {
    return {
      posts: [],
      baseUrl: process.env.BASE_URL,
      imgBaseUrl: process.env.IMG_URL,
      title: process.env.SITE_NAME,
      keyword: process.env.KEYWORD,
      page: null,
      paginatorType: 1,
      itemsPerPage: 100,
      catSlug: null,
      catTitle: null
    }
  },
  methods: {
    bgColor () {
      var bgColors = ['red', 'green', 'blue', 'black', 'maroon', 'navy', 'fuchsia',
        'purple', 'Brown', 'BlueViolet', 'CadetBlue', 'Chocolate', 'Coral',
        'CornflowerBlue', 'DarkBlue', 'DarkGoldenRod', 'DarkGreen', 'DarkMagenta',
        'DarkOliveGreen', 'DarkRed', 'DarkSlateBlue', 'DarkSlateGray', 'DarkViolet',
        'DeepPink', 'FireBrick', 'ForestGreen', 'Indigo', 'IndianRed', 'Maroon',
        'MidnightBlue']
      return 'background-color: ' + bgColors[Math.floor((Math.random() * bgColors.length))]
    }
  },
  asyncData ({ req, params, error }) {
    return axios.get('/cat/' + params.catSlug + '/' + (Number(params.page) || '0') + '/')
      .then((response) => {
        return { posts: response.data, catSlug: params.catSlug, catTitle: response.data[0].category_id.Title, page: Number(params.page) || 0 }
      })
      .catch((e) => {
        error({ statusCode: 500, message: e })
      })
  },
  components: {
    'paginator-component': Paginator,
    'ad-component': Ads
  },
  computed: {
    chunkPosts () {
      return chunk(this.posts, 2)
    },
    calcPages () {
      const pages = Math.floor(this.posts[0].total_posts / this.itemsPerPage)
      return pages
    }
  },
  head () {
    return {
      title: Number(this.$route.params.page) ? 'Page ' + Number(this.$route.params.page) + ' ' + this.catTitle + ' | ' + this.title : this.title
    }
  }
}
</script>

<style>
</style>