## WRGameVideos-API

** 因考虑到视频版权原因和 App Store 的审核问题，项目放弃 **

此项目本为一个视频聚合应用的 API 端，移动适配的 web 客户端请求数据生成页面，并通过Webview 组件加载至 iOS 应用中，少量的交互由 Javascript和 Objective-C 通信完成

Supply most model data via RESTFUL API, only JSON supported

## Third App

* register url - yourapidomain.com/apps/register (need login first)
* app review - yourapidomain.com/apps/<int:appid>/review (only administrator can approve a app)
* app list - yourapidomain.com/apps
* app detail - yourapidomain.com/apps/<int:appid> (you can find ==App Key== and ==App Secret== here)

## API request

### request access_token

* request url - yourapidomain.com/open/v1.0/access_token (GET method)
* url parameters
-   * grant_type - 'authorization_code'
-   * client_id - your app key
-   * tsamp - timestamp now (UTC+0)
-   * redirect_uri - callback url, must same as the redirect url provided when registered the app
-   * sign - a hmac hash string of 'app key+timestrap+redirect url', using App Secret as encrypt key

if everything is ok, return a json string including access_token:
```
{
  "access_token": "ab891e*************d20", 
  "expiration": 3600
}
```

or return kinds of errors like:
```
{
  "error": "incorrect_sign", 
  "message": "signature error"
}
```
### request user_access_token

if use API that need login, get user_access_token instead of app general access_token

first to redirect user to login page and get a timed authorization code

* request url - yourapidomain.com/open/v1.0/authorize (GET method)
* url parameters
-   * response_type - 'code'
-   * client_id - your app key
-   * tsamp - timestamp now (UTC+0)
-   * redirect_uri - callback url, must same as the redirect url provided when registered the app
-   * sign - a hmac hash string of 'app key+timestrap+redirect url', using App Secret as encrypt key


after user logged in, api site will redirect to the redirect_url you given with the timed authorization code, using the code to request info necessory, i.e. user_access_code

* request url - yourapidomain.com/open/v1.0/user_token (GET method)
* url parameters
-   * grant_type - 'authorization_code'
-   * client_id - your app key
-   * tsamp - timestamp now (UTC+0)
-   * redirect_uri - callback url, must same as the redirect url provided when registered the app
-   * code - a timed sign get from previous step

### request API using access_token

before API request, access_token will be verified, you can put you access_token in url parameters or HTTP headers(X-TOKEN:<your access_token>)
if an error occured, it will return:

```
{
  "error": "unauthorized", 
  "message": "Invalid access_token", 
  "request_token": "yourapidomain/open/v1.0/access_token"
}
```
you can forward to the value of `request_token` which is a url to request a access_token

a successful API request result is based on the specified API
