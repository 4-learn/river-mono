package cc.fourimpact.river

import android.Manifest
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.webkit.*
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import androidx.webkit.WebViewAssetLoader
import cc.fourimpact.river.ui.theme.RiverTheme

class MainActivity : ComponentActivity() {

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val allGranted = permissions.values.all { it }
        if (!allGranted) {
            Toast.makeText(this, "需要麥克風權限才能使用語音功能", Toast.LENGTH_LONG).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        requestPermissions()
        setContent { RiverTheme { WebViewComposable() } }
    }

    @Composable
    fun WebViewComposable() {
        AndroidView(
            factory = { context ->
                // 1) 建立 AssetLoader：把 assets 映射為一個 https 網域
                val assetLoader = WebViewAssetLoader.Builder()
                    // 最常見做法：assets -> https://appassets.androidplatform.net/assets/...
                    .addPathHandler(
                        "/assets/",
                        WebViewAssetLoader.AssetsPathHandler(context)
                    )
                    .build()

                WebView(context).apply {
                    WebView.setWebContentsDebuggingEnabled(true)

                    // 2) 攔截對 appassets.androidplatform.net 的請求，改由本地 assets 提供
                    webViewClient = object : WebViewClient() {
                        // API < 24
                        @Deprecated("Deprecated in API 24")
                        override fun shouldOverrideUrlLoading(view: WebView?, url: String?): Boolean {
                            url?.let { view?.loadUrl(it) }
                            return true
                        }

                        // API 24+
                        override fun shouldOverrideUrlLoading(
                            view: WebView?,
                            request: WebResourceRequest?
                        ): Boolean {
                            request?.url?.toString()?.let { view?.loadUrl(it) }
                            return true
                        }

                        // 重要：把對 appassets 的請求導到本地 assets
                        override fun shouldInterceptRequest(
                            view: WebView?,
                            request: WebResourceRequest?
                        ): WebResourceResponse? {
                            val url = request?.url ?: return null
                            return assetLoader.shouldInterceptRequest(url)
                        }

                        // 兼容舊 API
                        override fun shouldInterceptRequest(
                            view: WebView?,
                            url: String?
                        ): WebResourceResponse? {
                            val u = url ?: return null
                            return assetLoader.shouldInterceptRequest(Uri.parse(u))
                        }
                    }

                    webChromeClient = object : WebChromeClient() {
                        override fun onPermissionRequest(request: PermissionRequest?) {
                            // 允許 WebRTC 取用麥克風（你已做權限請求）
                            request?.grant(request?.resources)
                        }
                    }

                    settings.apply {
                        javaScriptEnabled = true
                        domStorageEnabled = true
                        mediaPlaybackRequiresUserGesture = false
                        userAgentString = "$userAgentString River"
                        allowFileAccess = true
                        allowContentAccess = true
                        mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
                        // 重點：不開啟 from-file 的萬用通行，安全性較好
                        // allowFileAccessFromFileURLs = false
                        // allowUniversalAccessFromFileURLs = false
                    }

                    // 3) 以「https 的本地域名」載入你的 index.html
                    //    對前端來說，現在的 Origin 是 https，可與你的 https API 正常做 CORS。
                    loadUrl("https://appassets.androidplatform.net/assets/index.html")
                }
            },
            modifier = Modifier.fillMaxSize()
        )
    }

    private fun requestPermissions() {
        val permissions = arrayOf(
            Manifest.permission.INTERNET,
            Manifest.permission.RECORD_AUDIO,
            Manifest.permission.MODIFY_AUDIO_SETTINGS
        )
        val needRequest = permissions.any {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        if (needRequest) requestPermissionLauncher.launch(permissions)
    }
}
