% % % % % % % % % % % % % % % % % % % % % % % % % % % % % % % % % % % % %
% % % LaTeX document class for the letter-formatted Human Tech paper % % %
% % % First edition 2015.10.30 by Chinook Mok % % % % % % % % % % % % % % %
% % % Modified edition 2015.11.28 by Seungwon Park % % % % % % % % % % % % % % %
% % % Modified by GSHS TeX Society(http://latex.gs.hs.kr) % % % % % % % %
% % % Modified by Hwijoon Lim % % % % % % % %
% % % % % % % % % % % % % % % % % % % % % % % % % % % % % % % % % % % % %
\ProvidesClass{humantech}
\RequirePackage{xkeyval}
\newcommand{\humentechnth}{1}
\DeclareOptionX{nth}[1]{\renewcommand{\humentechnth}{#1}}
\ProcessOptionsX
\LoadClass[twoside, 10pt, twocolumn]{article}

\usepackage{ifxetex} % 부득이하게 pdflatex을 사용해도 문제가 없도록 함
\usepackage[super]{nth}
\usepackage[T1]{fontenc}   % To use Times New Roman
\usepackage[utf8]{inputenc}% To use Times New Roman
\usepackage{mathptmx}      % To use Times New Roman
\usepackage{fancyhdr}      % To customize header and footer
\usepackage{ifthen}        % To distinguish the first page in header
\usepackage{abstract}      % To customize abstract
\usepackage{titlesec}      % To resize the titles of section/subsection/etc...
\usepackage{indentfirst}
\usepackage{kotex}         % korean paper
\usepackage{graphicx}
\usepackage[font=small,labelfont=bf,labelsep=period,skip=0pt]{caption} % Caption setup
\usepackage{ctable} % To customize table
% \usepackage{cite}     % To display citations as [1-3] instead of [1,2,3]
\usepackage[square,numbers,sort&compress]{natbib}
\usepackage{enumitem} % To remove the hanging indentation.
\usepackage{color} % To color header and footer as gray
\PassOptionsToPackage{hyphens}{url}\usepackage[hidelinks]{hyperref}

%%% following packages are optional %%%
\usepackage{amssymb}
\usepackage{amsmath}
\usepackage{amsthm} 
\usepackage[makeroom]{cancel} %To use cancelto of terms in equation
\usepackage{setspace}
\usepackage[a4paper, total={6in, 8in}]{geometry}
\DeclareMathAlphabet{\mathcal}{OMS}{cmsy}{m}{n}
%%%%%%%%%% page setting %%%%%%%%%%%
\setlength{\paperwidth}{210mm}
\setlength{\paperheight}{297mm}
\setlength{\hoffset}{-1in}
\setlength{\oddsidemargin}{15mm}
\setlength{\evensidemargin}{15mm}
\setlength{\textwidth}{180mm}
\setlength{\marginparsep}{0mm}
\setlength{\marginparwidth}{0mm}
\setlength{\voffset}{-1in}
\setlength{\topmargin}{20mm}
\setlength{\headheight}{12pt}
\setlength{\headsep}{12pt}
\setlength{\textheight}{241mm}
%\setlength{\footskip}{56pt}
%%%% two column setting %%%
\setlength{\columnsep}{20pt}
\setlength{\abovecaptionskip}{4mm}
%%%%%%%%% Header & Footer setting %%%%
\pagestyle{fancy}
%\rhead{}
%\chead{}
%\lhead{\ifthenelse{\value{page}=1}{\color{gray} \fontsize{12}{0}\selectfont $\bf{26}^{\bf th}\textbf{ HumanTech Paper Award}$}{\color{gray} \fontsize{9}{0}\selectfont $26^{\rd th}\textrm{ HumanTech Paper Award}$}}

\fancyhead[RO,LE]{\color{black!65} \fontsize{9}{0}\selectfont {\nth{\humentechnth} HumanTech Paper Award}}
\fancyhead[LO,RE]{}
\fancyfoot[LO]{\footnotesize 본 논문에 포함된 정보의 전부 또는 일부를 무단으로 제3자에게 공개, 배포, 복사 또는 사용하는 것은 엄격히 금지됩니다. \\ 본 논문의 모든 저작권은 저자에게 있습니다.}
\fancyfoot[RO]{\thepage}
\fancyfoot[LE]{\thepage}
\fancyfoot[RE]{\footnotesize 본 논문에 포함된 정보의 전부 또는 일부를 무단으로 제3자에게 공개, 배포, 복사 또는 사용하는 것은 엄격히 금지됩니다. \\ 본 논문의 모든 저작권은 저자에게 있습니다.}
\fancyfoot[C]{}
\renewcommand{\headrulewidth}{0pt}

\fancypagestyle{firstpage}{
\fancyhf{}
\fancyhead[L]{\color{black!65} \fontsize{12}{0}\selectfont {\nth{\humentechnth} HumanTech Paper Award}}
\fancyfoot[L]{\footnotesize 본 논문에 포함된 정보의 전부 또는 일부를 무단으로 제3자에게 공개, 배포, 복사 또는 사용하는 것은 엄격히 금지됩니다. \\ 본 논문의 모든 저작권은 저자에게 있습니다.}
\fancyfoot[R]{\thepage}
}

\makeatletter
\let\ps@plain\ps@fancy 
\makeatother

%%%%%%%% Title Setting %%%%%%
\makeatletter
\renewcommand{\maketitle}{
    \vspace*{0pt}\bgroup\setlength{\parindent}{0pt}
\begin{flushleft}
  \fontsize{20pt}{0}\selectfont{\textbf{\vspace{5pt}\@title}}
    \vspace{5pt}
\end{flushleft} \egroup
}
\makeatother
% \renewcommand{\maketitle}{
%   \twocolumn[\begin{@twocolumnfalse}
%     \vspace*{0pt}\bgroup\setlength{\parindent}{0pt}
% \begin{flushleft}
%   \fontsize{20pt}{0}\selectfont{\textbf{\vspace{5pt}\@title}}
%     \vspace{5pt}
% \end{flushleft}\egroup
% \end{@twocolumnfalse}]
% }
% \makeatother


%%%%%%% Abstract Setting %%%%%
\renewcommand{\abstractname}{(Abstract)\,}
\renewcommand{\absnamepos}{empty}
\renewenvironment{abstract}
 {
  \bfseries\list{\abstractname}{
    \setlength{\leftmargin}{0mm}
    \setlength{\labelsep}{0mm}
    \setlength{\rightmargin}{\leftmargin}
  }
   \item\relax
  }
 {\endlist 
    \vspace{-10mm}}
 

%%%%%% Section Title Setting %%%%%%% % Modified : added subsubsection
\titleformat*{\section}{\uppercase{\fontsize{11}{11}\selectfont\bfseries}}
\titleformat*{\subsection}{\fontsize{10}{10}\selectfont}
\titleformat*{\subsubsection}{\fontsize{10}{10}\selectfont}
\def\thesection{\arabic{section}.}
\def\thesubsection{\arabic{section}.\arabic{subsection}.}
\def\thesubsubsection{\arabic{section}.\arabic{subsection}.\arabic{subsubsection}.}
\makeatletter
\renewcommand{\@seccntformat}[1]{\csname the#1\endcsname\ }
\makeatother

%%%%% Caption(Figure/Table) Setting %%%%%%%
\captionsetup{figurename=Fig.} % Figure label (FIG: --> FIGURE)
\captionsetup[table]{
name=Table,   % Table label (Table --> TABLE)
singlelinecheck=off  % Left aligned
}

%%%%% Theorem Setting %%%%%
\theoremstyle{plain}
\newtheorem{thm}{Theorem}

\theoremstyle{definition}
\newtheorem{defn}{Definition}

%%%%% Declaration of Modified mathsymbol `mycdot' %%%%%
\newcommand*\mycdot{{\mkern -1mu\cdot\mkern -1mu}}

%%%% Reference Setting %%%%
\renewcommand\refname{REFERENCES}

\makeatletter
\renewcommand{\@biblabel}[1]{[#1]\hfill}
\makeatother

\makeatletter
\renewenvironment{thebibliography}[1]
     {\section*{\refname}%
      \@mkboth{\MakeUppercase\refname}{\MakeUppercase\refname}%
      \begin{enumerate}[label={[\arabic{enumi}]},itemindent=*,leftmargin=0pt,itemsep=-3pt]
      \@openbib@code
      \sloppy
      \clubpenalty4000
      \@clubpenalty \clubpenalty
      \widowpenalty4000
      \sfcode`\.\@m}
     {\def\@noitemerr
       {\@latex@warning{Empty `thebibliography' environment}}%
      \end{enumerate}}
\makeatother

\ifxetex
%한글 사용 옵션
\RequirePackage{xetexko}
\setmainfont[Ligatures=TeX]{Times New Roman}
\setmainhangulfont[BoldFont=*,BoldFeatures=FakeBold,%
	ItalicFont=*,ItalicFeatures=FakeSlant]{Batang}
\disablecjksymbolspacing
\nonfrenchspacing
\else
\fi
