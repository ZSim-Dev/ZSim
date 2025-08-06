import tseslint from '@electron-toolkit/eslint-config-ts'
import eslintConfigPrettier from '@electron-toolkit/eslint-config-prettier'
import eslintPluginReact from 'eslint-plugin-react'
import eslintPluginReactHooks from 'eslint-plugin-react-hooks'
import eslintPluginReactRefresh from 'eslint-plugin-react-refresh'

export default tseslint.config(
  {
    ignores: ['node_modules', 'dist', 'out'],
  },
  tseslint.configs.recommended,
  eslintPluginReact.configs.flat.recommended,
  eslintPluginReact.configs.flat['jsx-runtime'],
  {
    settings: {
      react: {
        version: 'detect',
      },
    },
  },
  {
    stylistic: {
      indent: 2,
      quotes: 'single',
    },
    rules: {
      // 顶层函数允许使用箭头函数
      'antfu/top-level-function': 'off',
      // 断行符号使用 CRLF
      'style/linebreak-style': ['error', 'windows'],
      // 文件末尾保留空行
      'style/eol-last': 'error',
    },
  },
  {
    files: ['**/*.{ts,tsx}'],
    plugins: {
      'react-hooks': eslintPluginReactHooks,
      'react-refresh': eslintPluginReactRefresh,
    },
    rules: {
      ...eslintPluginReactHooks.configs.recommended.rules,
      ...eslintPluginReactRefresh.configs.vite.rules,
      // React Compiler 规则
      'react-hooks/react-compiler': 'error',
      // 记得清理 console
      'no-console': 'warn',
      // 默认参数必须放在最后
      'default-param-last': 'error',
      // 一般情况下不允许使用 any
      '@typescript-eslint/no-explicit-any': 'warn',
      // 命名规范
      '@typescript-eslint/naming-convention': [
        'error',
        // TS interface 只允许大驼峰
        {
          selector: 'interface',
          format: ['PascalCase'],
          leadingUnderscore: 'forbid',
        },
        // TS Type 只允许大驼峰
        {
          selector: 'typeLike',
          format: ['PascalCase'],
          leadingUnderscore: 'forbid',
        },
        // 变量只允许大小驼峰、全大写下划线、全小写下划线
        {
          selector: 'variable',
          format: ['PascalCase', 'camelCase', 'UPPER_CASE', 'snake_case'],
          leadingUnderscore: 'allow',
          trailingUnderscore: 'allow',
        },
      ],
    },
  },
  {
    files: ['**/*.vue'],
    rules: {
      // 组件名称至少由 2 个单词组成
      'vue/multi-word-component-names': 'error',
      // 组件定义名称只允许连字符风格
      'vue/component-definition-name-casing': ['error', 'kebab-case'],
      // 组件属性名称只允许小驼峰风格
      'vue/prop-name-casing': ['error', 'camelCase'],
      // 允许在相同作用域范围从对象获取响应值
      'vue/no-ref-object-reactivity-loss': 'off',
      // 未使用的值必须使用下划线开头
      'vue/no-unused-vars': [
        'error',
        {
          ignorePattern: '^_',
        },
      ],
    },
  },
  {
    files: ['**/*.json', '**/*.jsonc'],
    rules: {
      // json key 排序
      'jsonc/sort-keys': ['warn', 'asc'],
    },
  },
  eslintConfigPrettier
)
